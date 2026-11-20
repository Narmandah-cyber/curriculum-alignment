"""Тэмдэглэгчдийн тохироо ба системийн үнэлгээ (Бүлэг 4, СА3, СА4). Хариуцагч: Б.

agreement()      — хоёр тэмдэглэгчийн Cohen's kappa (тэмдэглэгээний найдвартай байдал)
evaluate_links() — СА3: дүрэм / embedding / хосолсон аргыг links_gold.csv-тэй харьцуулна.
                   θ-г dev хэсэгт F1-ээр сонгоод test хэсэгт P, R, F1-ийг тайлагнана.
evaluate_bloom() — СА4: Блумын түвшний macro-F1, kappa, будлиантын матриц (confusion matrix).
evaluate_gaps()  — СА4: түвшний зөрүү (доогуур / нийцсэн / дээгүүр)-г зөв илрүүлсэн эсэх.

Систем талын тооцоо нь өгөгдлийн сангүйгээр, файл дахь текст дээр шууд хийгдэнэ (давтагдахуйц, ФБШ-07).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from app.evaluation import metrics as M
from app.evaluation.annotation import ASSESSMENT_TYPES, BLOOM_LABELS, LINK_LABELS, read_annotations, read_csv

POSITIVE = ("direct", "partial")
GAP_LABELS = ("below", "match", "above")


# --------------------------------------------------------------------------- Тэмдэглэгчдийн тохироо
def agreement(path_a: Path, path_b: Path, task: str) -> dict:
    a, b = read_annotations(path_a, task), read_annotations(path_b, task)
    keys = sorted(a.keys() & b.keys())
    if len(keys) != len(a) or len(keys) != len(b):
        raise ValueError("Хоёр файлын мөрүүд зөрүүтэй")
    col = "label" if task == "links" else "level"
    la, lb = [a[k][col] for k in keys], [b[k][col] for k in keys]
    out = {"task": task, "n": len(keys), "observed": M.accuracy(la, lb), "kappa": M.cohen_kappa(la, lb),
           "labels": list(LINK_LABELS if task == "links" else BLOOM_LABELS)}
    out["interpretation"] = M.landis_koch(out["kappa"])
    out["confusion"] = M.confusion(la, lb, out["labels"])
    if task == "links":
        ba, bb = [x in POSITIVE for x in la], [x in POSITIVE for x in lb]
        out["kappa_binary"] = M.cohen_kappa(ba, bb)          # холбоотой эсэх (хүчийг тооцохгүй)
    else:
        out["adjacent"] = sum(1 for x, y in zip(la, lb, strict=False) if abs(int(x) - int(y)) <= 1) / len(keys) if keys else 0.0
    out["disagreements"] = [{"id": k, "A": a[k][col], "B": b[k][col]} for k in keys if a[k][col] != b[k][col]]
    return out


# --------------------------------------------------------------------------- СА3: холбоос
@dataclass
class MethodResult:
    method: str
    available: bool
    reason: str | None = None
    seconds: float = 0.0
    threshold: float | None = None          # dev дээр сонгосон θ
    direct_threshold: float | None = None   # dev дээр сонгосон θ_d
    test: M.PRF | None = None
    test_at_default: M.PRF | None = None    # тохиргооны θ (жишээ нь 0.5) дээрх үр дүн
    strength_macro_f1: float | None = None  # direct / partial / none гурван ангиллын macro-F1 (test)
    kappa_vs_gold: float | None = None
    curve: list[dict] = field(default_factory=list)


def _scorer(method: str, embedder, lam: float):
    from app.services.analysis.course import EmbeddingScorer, HybridScorer, RuleScorer
    if method == "rule":
        return RuleScorer()
    if embedder is None:
        from app.core.config import get_settings
        from app.services.nlp.similarity import Embedder
        embedder = Embedder(get_settings().embedding_model)
    return EmbeddingScorer(embedder) if method == "embedding" else HybridScorer(embedder, lam)


def score_pairs(method: str, clo_texts: list[str], item_texts: list[str], embedder=None, lam: float = 0.7) -> list[float]:
    """Хос бүрийн оноо. Embedding боломжгүй бол алдаа (NotImplementedError, ImportError …) дамжуулна."""
    sc = _scorer(method, embedder, lam)
    sc.prepare(clo_texts, item_texts)
    return [round(sc.score(i, i, c, t), 4) for i, (c, t) in enumerate(zip(clo_texts, item_texts, strict=False))]


def _present(*seqs) -> list[str]:
    """Алтан стандарт эсвэл таамагт байгаа ангиллууд (байхгүй ангиллыг F1=0 гэж дунджид оруулахгүй)."""
    seen = set().union(*map(set, seqs))
    return [lab for lab in LINK_LABELS if lab in seen]


def _strength(s: float, theta: float, theta_d: float) -> str:
    return "none" if s < theta else ("direct" if s >= theta_d else "partial")


def _best_direct(scores: list[float], gold3: list[str], theta: float, candidates: list[float]) -> float:
    """θ_d: dev дээр direct / partial / none гурван ангиллын macro-F1-ийг хамгийн их болгох утга."""
    def f1(td: float) -> float:
        pred = [_strength(s, theta, td) for s in scores]
        return round(M.macro_f1(gold3, pred, _present(gold3, pred)), 10)
    return max(candidates, key=lambda td: (f1(td), -td))


def evaluate_links(gold_path: Path, methods=("rule", "embedding", "hybrid"), embedder=None,
                   lam: float = 0.7, default_threshold: float = 0.5, thresholds=None) -> dict:
    gold = list(read_annotations(gold_path, "links").values())
    if not gold:
        raise ValueError("links_gold.csv хоосон")
    thresholds = thresholds or M.grid(0.05, 0.95, 0.05)
    dev = [r for r in gold if r.get("split") == "dev"]
    test = [r for r in gold if r.get("split") == "test"]
    note = None
    if not dev or not test:
        dev = test = gold
        note = "dev/test хуваалт алга тул θ-г бүх өгөгдөл дээр сонгосон (үр дүн өөдрөг байж болно)."

    results = []
    for m in methods:
        res = MethodResult(method=m, available=True)
        try:
            t0 = time.perf_counter()
            s_dev = score_pairs(m, [r["clo_text"] for r in dev], [r["item_text"] for r in dev], embedder, lam)
            s_test = score_pairs(m, [r["clo_text"] for r in test], [r["item_text"] for r in test], embedder, lam)
            res.seconds = round(time.perf_counter() - t0, 3)
        except Exception as e:                 # А6 хэрэгжээгүй, загвар татагдаагүй
            res.available, res.reason = False, f"{type(e).__name__}: {e}"
            results.append(res)
            continue
        g_dev = [r["label"] in POSITIVE for r in dev]
        g_test = [r["label"] in POSITIVE for r in test]
        best = M.best_threshold(s_dev, g_dev, thresholds)
        res.threshold = best["threshold"]
        res.curve = M.threshold_curve(s_dev, g_dev, thresholds)
        # θ_d: θ-оос дээш, dev дээр 3 ангиллын macro-F1-ийг хамгийн их болгох утга
        cand = [t for t in thresholds if t >= res.threshold] or [res.threshold]
        res.direct_threshold = _best_direct(s_dev, [r["label"] for r in dev], res.threshold, cand)
        res.test = M.prf(g_test, [s >= res.threshold for s in s_test])
        res.test_at_default = M.prf(g_test, [s >= default_threshold for s in s_test])
        pred3 = [_strength(s, res.threshold, res.direct_threshold) for s in s_test]
        gold3 = [r["label"] for r in test]
        res.strength_macro_f1 = M.macro_f1(gold3, pred3, _present(gold3, pred3))
        res.kappa_vs_gold = M.cohen_kappa([r["label"] for r in test], pred3)
        results.append(res)
    return {"n": len(gold), "n_dev": len(dev), "n_test": len(test),
            "positives": sum(r["label"] in POSITIVE for r in gold), "note": note,
            "default_threshold": default_threshold, "results": results}


# --------------------------------------------------------------------------- СА4: Блумын түвшин
def predict_levels(texts: list[str], verbs: dict[str, int] | None = None) -> list[tuple[int | None, str]]:
    """(түвшин, эх: verb | classifier) — системийн Б4 модулиар."""
    from app.services.bloom.classifier import BloomClassifier
    from app.services.bloom.levels import BloomDictionary, assess, load_seed_verbs
    d, clf = BloomDictionary(verbs if verbs is not None else load_seed_verbs()), BloomClassifier()
    out = []
    for t in texts:
        r = assess(t, d, clf)
        out.append((r.level, r.source) if r else (None, "none"))
    return out


def evaluate_bloom(gold_path: Path, verbs: dict[str, int] | None = None) -> dict:
    gold = list(read_annotations(gold_path, "bloom").values())
    t0 = time.perf_counter()
    pred = predict_levels([r["text"] for r in gold], verbs)
    secs = round(time.perf_counter() - t0, 3)
    g = [r["level"] for r in gold]
    p = [str(lv) if lv else "0" for lv, _ in pred]
    labels = [lab for lab in BLOOM_LABELS if lab in g]
    by_source = {}
    for src in ("verb", "classifier"):
        idx = [i for i, (_, s) in enumerate(pred) if s == src]
        by_source[src] = {"n": len(idx), "accuracy": M.accuracy([g[i] for i in idx], [p[i] for i in idx]) if idx else None}
    subsets = {}
    for name, cond in (("clo", lambda r: r["kind"] == "clo"), ("assessment", lambda r: r["kind"] in ASSESSMENT_TYPES)):
        idx = [i for i, r in enumerate(gold) if cond(r)]
        if idx:
            subsets[name] = {"n": len(idx), "macro_f1": M.macro_f1([g[i] for i in idx], [p[i] for i in idx], labels)}
    return {"n": len(gold), "seconds": secs, "labels": labels, "macro_f1": M.macro_f1(g, p, labels),
            "accuracy": M.accuracy(g, p), "kappa": M.cohen_kappa(g, p),
            "adjacent": sum(1 for x, y in zip(g, p, strict=False) if abs(int(x) - int(y)) <= 1) / len(g) if g else 0.0,
            "per_class_f1": M.per_class_f1(g, p, labels), "confusion": M.confusion(g, p, labels),
            "by_source": by_source, "subsets": subsets}


def evaluate_gaps(links_gold: Path, bloom_gold: Path, verbs: dict[str, int] | None = None) -> dict:
    """Алтан стандартаар холбоотой (CLO, үнэлгээний элемент) хос бүрт Δ-ийн ангиллыг харьцуулна.

    Жинхэнэ Δ = алтан түвшнүүдээр, систем Δ = системийн түвшнүүдээр. Холбоосыг алтан стандартаас авдаг тул
    энэ нь зөвхөн түвшин тогтоолтын алдааг хэмжинэ (холбоос олох алдаа СА3-т тусдаа).
    """
    from app.services.bloom.levels import level_gap
    links = read_annotations(links_gold, "links")
    bloom = read_annotations(bloom_gold, "bloom")
    pairs = [r for r in links.values() if r["label"] in POSITIVE and r["item_type"] in ASSESSMENT_TYPES
             and f"clo:{r['clo_id']}" in bloom and f"item:{r['item_id']}" in bloom]
    if not pairs:
        return {"n": 0}
    objs = sorted({f"clo:{r['clo_id']}" for r in pairs} | {f"item:{r['item_id']}" for r in pairs})
    pred = dict(zip(objs, [lv or 1 for lv, _ in predict_levels([bloom[o]["text"] for o in objs], verbs)], strict=False))
    gold_gap = [level_gap(int(bloom[f"item:{r['item_id']}"]["level"]), int(bloom[f"clo:{r['clo_id']}"]["level"])) for r in pairs]
    pred_gap = [level_gap(pred[f"item:{r['item_id']}"], pred[f"clo:{r['clo_id']}"]) for r in pairs]
    return {"n": len(pairs), "accuracy": M.accuracy(gold_gap, pred_gap),
            "macro_f1": M.macro_f1(gold_gap, pred_gap, GAP_LABELS), "kappa": M.cohen_kappa(gold_gap, pred_gap),
            "below": M.prf([x == "below" for x in gold_gap], [x == "below" for x in pred_gap]),
            "confusion": M.confusion(gold_gap, pred_gap, GAP_LABELS)}


def gold_ready(path: Path, task: str) -> None:
    """gold.csv-д хэлэлцээгүй (хоосон) мөр үлдсэн бол үнэлгээ эхлүүлэхгүй."""
    col = "label" if task == "links" else "level"
    empty = [r for r in read_csv(path) if not r.get(col)]
    if empty:
        raise ValueError(f"{path.name}: {len(empty)} мөрийн «{col}» хоосон (disputed=1 мөрүүдийг хэлэлцэж бөглөнө үү)")
