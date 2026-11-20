"""Control: ХичээлийнШинжилгээ (UC3). Хариуцагч: Б5. Бүлэг 2: Зураг (UC3 дараалал), (хичээлийн үйл ажиллагаа).

Аргын нэр ↔ Бүлэг 3-ын control класс:
    create_run / execute ↔ эхлүүлэх(v, арга)
    _settings            ↔ тохиргооАчаалах()
    _prepare             ↔ текстБэлтгэх()
    _bloom_levels        ↔ блумТүвшинТодорхойлох()
    scorer.score         ↔ сэдвийнОнооТооцох() / хосолсонОнооТооцох()
    _propose_link        ↔ холбоосСаналҮүсгэх()
    _clo_plo             ↔ CLO_PLOСаналГаргах() (ФШ-14)
    level_gap            ↔ түвшнийЗөрүүАнгилах()
    gaps()               ↔ хамрагдаагүйТэмдэглэх() / зорилгогүйТэмдэглэх()
    _progress            ↔ явцШинэчлэх()
    execute (commit)     ↔ үрДүнХадгалах()

Оноо тооцох аргууд Strategy загвараар (ФБШ-10): RuleScorer, EmbeddingScorer, HybridScorer.
Шинэ арга нэмэхдээ Scorer-ийг өргөтгөж SCORERS-д бүртгэнэ, бусад кодыг өөрчлөхгүй.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AnalysisRun, Clo, CourseVersion, LearningItem, Link, Plo, ProgramCourse, Setting
from app.services.bloom.classifier import BloomClassifier
from app.services.bloom.levels import BloomDictionary, assess, level_gap, load_dictionary
from app.services.nlp.preprocess import tokens
from app.services.nlp.similarity import Embedder, cosine, hybrid_score, keyword_score

log = logging.getLogger(__name__)

# Үнэлгээний элемент: лекцээс бусад (ФШ-12, ФШ-13)
ASSESSMENT_TYPES = ("lab", "assignment", "exam")

# Түр стоп үг ба үндэс — А6 (services/nlp) бэлэн болмогц тэндээс авна.
_STOP = {"ба", "болон", "нь", "юм", "бол", "гэж", "вэ", "юу", "ч", "энэ", "тэр", "the", "and", "of", "to", "a", "in"}
_STEM_LEN = 5


def stems(text: str) -> dict[str, str]:
    """{үндэс: анхны үг}. Залгамал хэлний энгийн суурь: үгийн эхний 5 тэмдэгт (TODO А6: морфологи)."""
    out: dict[str, str] = {}
    for t in tokens(text):
        if t in _STOP or len(t) < 2:
            continue
        out.setdefault(t[:_STEM_LEN], t)
    return out


def matched_terms(a: str, b: str) -> list[str]:
    """Таарсан үгс (ФШ-24): хоёр текстэд ижил үндэстэй үгс, a-гийн хэлбэрээр."""
    sa, sb = stems(a), stems(b)
    return [sa[k] for k in sa if k in sb]


def item_text(item: LearningItem) -> str:
    """СургалтынЭлемент.шинжлэхТекстАвах(): гарчиг + тайлбар + асуулт."""
    return " ".join(x for x in (item.title, item.text, item.question_text) if x)


# --------------------------------------------------------------------------- Strategy (ФБШ-10)
class Scorer:
    """Сэдвийн ижил төстэй байдлын нийтлэг интерфейс."""
    name = "base"

    def prepare(self, clo_texts: list[str], item_texts: list[str]) -> None:   # noqa: B027
        """Хэрэгтэй бол embedding-ийг нэг дор тооцно."""

    def score(self, i: int, j: int, clo_text: str, item_text_: str) -> float:
        raise NotImplementedError


class RuleScorer(Scorer):
    """Дүрэмд суурилсан: үндэсний түлхүүр үгийн давхцал (Jaccard)."""
    name = "rule"

    def score(self, i, j, clo_text, item_text_):
        return keyword_score(" ".join(stems(clo_text)), " ".join(stems(item_text_)))


class EmbeddingScorer(Scorer):
    """Олон хэлт embedding загварын косинус (А6-ийн Embedder)."""
    name = "embedding"

    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self._c: list[list[float]] = []
        self._i: list[list[float]] = []

    def prepare(self, clo_texts, item_texts):
        vecs = self.embedder.encode(clo_texts + item_texts)
        self._c, self._i = vecs[:len(clo_texts)], vecs[len(clo_texts):]

    def score(self, i, j, clo_text, item_text_):
        return max(0.0, min(1.0, cosine(self._c[i], self._i[j])))


class HybridScorer(Scorer):
    """s = λ·s_emb + (1−λ)·s_rule."""
    name = "hybrid"

    def __init__(self, embedder: Embedder, lam: float):
        self.emb, self.rule, self.lam = EmbeddingScorer(embedder), RuleScorer(), lam

    def prepare(self, clo_texts, item_texts):
        self.emb.prepare(clo_texts, item_texts)

    def score(self, i, j, clo_text, item_text_):
        return hybrid_score(self.emb.score(i, j, clo_text, item_text_),
                            self.rule.score(i, j, clo_text, item_text_), self.lam)


@dataclass
class AnalysisSettings:
    threshold: float          # θ
    direct_threshold: float   # шууд/хэсэгчлэн хил
    lam: float                # λ
    embedding_model: str
    llm_enabled: bool


# --------------------------------------------------------------------------- Control
class CourseAnalysis:
    def __init__(self, db: Session, embedder: Embedder | None = None,
                 dictionary: BloomDictionary | None = None, classifier: BloomClassifier | None = None):
        self.db = db
        self._embedder = embedder
        self._dictionary = dictionary
        self._classifier = classifier or BloomClassifier()
        self.notice: str | None = None

    # -- тохиргооАчаалах()
    def _settings(self) -> AnalysisSettings:
        s = get_settings()
        stored = {r.key: r.value for r in self.db.scalars(select(Setting))}

        def num(key: str, default: float) -> float:
            try:
                return float(stored[key]) if stored.get(key) not in (None, "") else default
            except ValueError:
                return default
        return AnalysisSettings(
            threshold=num("link_threshold", s.link_threshold),
            direct_threshold=num("direct_threshold", s.direct_threshold),
            lam=num("hybrid_lambda", s.hybrid_lambda),
            embedding_model=stored.get("embedding_model") or s.embedding_model,
            llm_enabled=(stored.get("llm_enabled") or str(s.llm_enabled)).lower() in ("1", "true", "yes"),
        )

    def _scorer(self, method: str, cfg: AnalysisSettings, clo_texts: list[str], item_texts: list[str]) -> Scorer:
        """Аргаар Scorer сонгоно. Embedding загвар бэлэн биш бол дүрмийн аргаар үргэлжлүүлнэ."""
        if method == "rule":
            sc: Scorer = RuleScorer()
        else:
            emb = self._embedder or Embedder(cfg.embedding_model)
            sc = EmbeddingScorer(emb) if method == "embedding" else HybridScorer(emb, cfg.lam)
        try:
            sc.prepare(clo_texts, item_texts)
            return sc
        except Exception as e:   # NotImplementedError (А6), ImportError, загвар татагдаагүй
            log.warning("Embedding ашиглах боломжгүй (%s): дүрмийн аргаар үргэлжлүүлэв", e)
            self.notice = "Embedding загвар бэлэн биш тул дүрэмд суурилсан аргаар шинжлэв."
            return RuleScorer()

    # -- эхлүүлэх()
    def create_run(self, version_id: int, method: str, user_id: int) -> AnalysisRun:
        if not self.db.get(CourseVersion, version_id):
            raise ValueError("Хувилбар олдсонгүй")
        run = AnalysisRun(scope="course", version_id=version_id, method=method,
                          threshold=self._settings().threshold, status="running", progress=0, started_by=user_id)
        self.db.add(run)
        self.db.commit()
        return run

    def start(self, version_id: int, method: str, user_id: int, llm: bool = False) -> AnalysisRun:
        """Синхрон хувилбар (тест, жижиг өгөгдөл)."""
        run = self.create_run(version_id, method, user_id)
        return self.execute(run.id, llm=llm)

    def execute(self, run_id: int, llm: bool = False) -> AnalysisRun:
        run = self.db.get(AnalysisRun, run_id)
        try:
            self._execute(run, llm)
            run.status, run.progress = "done", 100
        except Exception:
            log.exception("Хичээлийн шинжилгээ амжилтгүй (run=%s)", run_id)
            self.db.rollback()
            run = self.db.get(AnalysisRun, run_id)
            run.status = "failed"
        run.finished_at = datetime.now(UTC)
        self.db.commit()
        return run

    def _execute(self, run: AnalysisRun, llm: bool) -> None:
        cfg = self._settings()
        clos = list(self.db.scalars(select(Clo).where(Clo.version_id == run.version_id).order_by(Clo.code)))
        items = list(self.db.scalars(select(LearningItem).where(LearningItem.version_id == run.version_id)
                                     .order_by(LearningItem.id)))
        if not clos or not items:
            raise ValueError("CLO эсвэл сургалтын элемент байхгүй")
        if llm and not cfg.llm_enabled:
            self.notice = (self.notice + " " if self.notice else "") + "LLM тайлбаргүйгээр үргэлжлүүлсэн (ФБШ-06)."

        self._bloom_levels(clos, items)
        clo_texts, item_texts = self._prepare(clos, items)
        scorer = self._scorer(run.method, cfg, clo_texts, item_texts)
        if scorer.name != run.method:
            run.method = scorer.name

        # Өмнөх баталгаажаагүй саналуудыг шинэчилнэ; баталгаажсан/татгалзсаныг хөндөхгүй (UC3 5а)
        clo_ids = [c.id for c in clos]
        self.db.execute(delete(Link).where(Link.source_type == "clo", Link.target_type == "item",
                                           Link.status == "proposed", Link.source_id.in_(clo_ids)))
        decided = {(lk.source_id, lk.target_id) for lk in self.db.scalars(
            select(Link).where(Link.source_type == "clo", Link.target_type == "item",
                               Link.source_id.in_(clo_ids), Link.status.in_(("confirmed", "rejected"))))}

        plos = course_plos(self.db, run.version_id)
        total, done = len(clos) * (len(items) + len(plos)), 0
        for i, c in enumerate(clos):
            for j, it in enumerate(items):
                s = round(scorer.score(i, j, clo_texts[i], item_texts[j]), 4)
                if s >= cfg.threshold and (c.id, it.id) not in decided:
                    self._propose_link(run, c, it, s, cfg)
                done += 1
            self._progress(run, done, total)
        if plos:
            self._clo_plo(run, cfg, clos, clo_texts, plos, done, total)

    def _prepare(self, clos: list[Clo], items: list[LearningItem]) -> tuple[list[str], list[str]]:
        """текстБэлтгэх()."""
        return [c.text for c in clos], [item_text(it) for it in items]

    def _bloom_levels(self, clos: list[Clo], items: list[LearningItem]) -> None:
        """блумТүвшинТодорхойлох(): гараар зассан (manual) түвшинг хөндөхгүй (ФШ-21)."""
        dictionary = self._dictionary or load_dictionary(self.db)
        for obj, text in [(c, c.text) for c in clos] + [(it, item_text(it)) for it in items]:
            if obj.level_source == "manual" and obj.bloom_level:
                continue
            r = assess(text, dictionary, self._classifier)
            if r:
                obj.bloom_level, obj.level_source = r.level, "auto"

    def _propose_link(self, run: AnalysisRun, clo: Clo, item: LearningItem, s: float,
                      cfg: AnalysisSettings) -> Link:
        """холбоосСаналҮүсгэх() + түвшнийЗөрүүАнгилах()."""
        gap = level_gap(item.bloom_level or 1, clo.bloom_level or 1)
        lk = Link(run_id=run.id, source_type="clo", source_id=clo.id, target_type="item", target_id=item.id,
                  strength="direct" if s >= cfg.direct_threshold else "partial", score=s, method=run.method,
                  level_gap=gap, status="proposed")
        self.db.add(lk)
        return lk

    def _clo_plo(self, run: AnalysisRun, cfg: AnalysisSettings, clos: list[Clo], clo_texts: list[str],
                 plos: list[Plo], done: int, total: int) -> None:
        """CLO_PLOСаналГаргах() (ФШ-14): CLO бүрийг хичээл хамаарах хөтөлбөрүүдийн PLO-той харьцуулна.

        CLO–элементийн адил арга, босгыг хэрэглэнэ. Δ = L(CLO) − L(PLO): хичээлийн үр дүн хөтөлбөрийн
        үр дүнгээс доогуур түвшинд байвал «доогуур». PLO-ийн түвшинг өөрчлөхгүй (хөтөлбөрийн тал — А).
        """
        plo_texts = [p.text for p in plos]
        scorer = self._scorer(run.method, cfg, clo_texts, plo_texts)
        clo_ids = [c.id for c in clos]
        self.db.execute(delete(Link).where(Link.source_type == "clo", Link.target_type == "plo",
                                           Link.status == "proposed", Link.source_id.in_(clo_ids)))
        decided = {(lk.source_id, lk.target_id) for lk in self.db.scalars(
            select(Link).where(Link.source_type == "clo", Link.target_type == "plo",
                               Link.source_id.in_(clo_ids), Link.status.in_(("confirmed", "rejected"))))}
        dictionary = self._dictionary or load_dictionary(self.db)
        plo_levels = {p.id: p.bloom_level or _level(p.text, dictionary, self._classifier) for p in plos}
        for i, c in enumerate(clos):
            for j, p in enumerate(plos):
                s = round(scorer.score(i, j, clo_texts[i], plo_texts[j]), 4)
                if s >= cfg.threshold and (c.id, p.id) not in decided:
                    self.db.add(Link(run_id=run.id, source_type="clo", source_id=c.id, target_type="plo",
                                     target_id=p.id, strength="direct" if s >= cfg.direct_threshold else "partial",
                                     score=s, method=scorer.name,
                                     level_gap=level_gap(c.bloom_level or 1, plo_levels[p.id] or 1),
                                     status="proposed"))
                done += 1
            self._progress(run, done, total)

    def _progress(self, run: AnalysisRun, done: int, total: int) -> None:
        """явцШинэчлэх() (ФБШ-02)."""
        run.progress = min(99, int(done * 100 / total))
        self.db.commit()


def _level(text: str, dictionary: BloomDictionary, classifier: BloomClassifier) -> int | None:
    r = assess(text, dictionary, classifier)
    return r.level if r else None


def course_plos(db: Session, version_id: int) -> list[Plo]:
    """Хувилбарын хичээл хамааруулсан (program_courses, А4) хөтөлбөрүүдийн PLO."""
    v = db.get(CourseVersion, version_id)
    if v is None:
        return []
    program_ids = select(ProgramCourse.program_id).where(ProgramCourse.course_id == v.course_id)
    return list(db.scalars(select(Plo).where(Plo.program_id.in_(program_ids)).order_by(Plo.program_id, Plo.code)))


# --------------------------------------------------------------------------- Үр дүн унших (UC5)
def version_links(db: Session, version_id: int, target_type: str = "item") -> list[Link]:
    """Хувилбарын CLO-оос гарах холбоосууд: target_type="item" (ФШ-10) эсвэл "plo" (ФШ-14)."""
    clo_ids = select(Clo.id).where(Clo.version_id == version_id)
    return list(db.scalars(select(Link).where(Link.source_type == "clo", Link.target_type == target_type,
                                              Link.source_id.in_(clo_ids))))


def gaps(db: Session, version_id: int) -> dict:
    """Түвшний зөрүү (ФШ-12), хамрагдаагүй CLO, зорилгогүй элемент (ФШ-13).

    - хамрагдаагүй CLO: ямар ч үнэлгээний элементтэй БАТАЛГААЖСАН холбоосгүй
    - зорилгогүй элемент: ямар ч CLO-той холбоосгүй (татгалзсанаас бусад) үнэлгээний элемент
    - түвшний зөрүү: татгалзаагүй, үнэлгээний элементтэй холбоосын Δ
    """
    clos = {c.id: c for c in db.scalars(select(Clo).where(Clo.version_id == version_id).order_by(Clo.code))}
    items = {i.id: i for i in db.scalars(select(LearningItem).where(LearningItem.version_id == version_id)
                                         .order_by(LearningItem.id))}
    assessments = {k: v for k, v in items.items() if v.type in ASSESSMENT_TYPES}
    links = [lk for lk in version_links(db, version_id) if lk.status != "rejected" and lk.target_id in items]
    to_assess = [lk for lk in links if lk.target_id in assessments and lk.source_id in clos]

    counts = {"match": 0, "below": 0, "above": 0}
    level_rows = []
    for lk in to_assess:
        clo, it = clos[lk.source_id], assessments[lk.target_id]
        g = level_gap(it.bloom_level or 1, clo.bloom_level or 1)   # түвшин гараар зассан бол шинэчилнэ
        counts[g] += 1
        if g != "match":
            level_rows.append((lk, clo, it, g))
    order = {"below": 0, "above": 1}
    level_rows.sort(key=lambda r: (order[r[3]], r[1].code))

    confirmed_clos = {lk.source_id for lk in to_assess if lk.status == "confirmed"}
    proposed_clos = {lk.source_id for lk in to_assess if lk.status == "proposed"}
    linked_items = {lk.target_id for lk in links}
    return {
        **counts,
        "level_gaps": level_rows,
        "uncovered": [(c, c.id in proposed_clos) for cid, c in clos.items() if cid not in confirmed_clos],
        "unaligned": [it for iid, it in assessments.items() if iid not in linked_items],
    }


def summary(db: Session, version_id: int) -> dict:
    """Хянах самбарын хураангуй (proto-02)."""
    analyzed = db.scalar(select(AnalysisRun.id).where(AnalysisRun.version_id == version_id,
                                                      AnalysisRun.status == "done").limit(1)) is not None
    g = gaps(db, version_id)
    n_clo = len(g["uncovered"])
    total = db.scalar(select(func.count(Clo.id)).where(Clo.version_id == version_id)) or 0
    proposed = sum(1 for lk in version_links(db, version_id) if lk.status == "proposed")
    return {
        "analyzed": analyzed,
        "coverage": round((total - n_clo) / total, 3) if total else 0.0,
        "proposed": proposed,
        "uncovered_clos": n_clo if analyzed else 0,
        "level_gaps": g["below"] + g["above"],
    }
