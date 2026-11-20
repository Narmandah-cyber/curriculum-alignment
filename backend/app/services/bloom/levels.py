"""Блумын түвшин (ФШ-11, ФШ-12, ФШ-21). Control: БлумынТоль, ХичээлийнШинжилгээ. Хариуцагч: Б4, Б5.

Түвшин тогтоох дараалал (Бүлэг 2, Зураг: хичээлийн шинжилгээний үйл ажиллагааны баруун урсгал):
    1. Текстээс үйл үг ялгаж, Блумын тольд таарвал толийн түвшинг ононо  (үйлҮгЯлгах, түвшинТаних)
    2. Таарахгүй бол ангилагчийн тогтоосон түвшинг ононо               (classifier.BloomClassifier)

Аргын нэр ↔ Бүлэг 3-ын control класс «БлумынТоль»:
    BloomDictionary.extract_verbs  ↔ үйлҮгЯлгах()
    BloomDictionary.detect         ↔ түвшинТаних()
    level_name                     ↔ түвшинНэрАвах()
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path

from app.services.nlp.preprocess import normalize, tokens

LEVELS = {1: "санах", 2: "ойлгох", 3: "хэрэглэх", 4: "задлан шинжлэх", 5: "үнэлэх", 6: "бүтээх"}

# Үйл үгээс үүссэн нэр үгийн дагавар: «үнэлгээ», «шинжилгээ», «ашиглалт» нь үйл үг биш тул тааруулахгүй.
_NOUN_SUFFIXES = ("гээ", "гаа", "гоо", "гөө", "лгээ", "лгаа", "алт", "элт", "олт", "өлт", "лт")

SEED_VERBS_FILE = Path(os.getenv("SEED_DIR", Path(__file__).resolve().parents[4] / "data" / "seed")) / "bloom_verbs.csv"


def level_name(level: int | None) -> str:
    """түвшинНэрАвах(): 1–6 → «санах» ... «бүтээх»."""
    return LEVELS.get(level or 0, "")


def verb_stem(verb: str) -> str:
    """Үйл үгийн үндэс: «тайлбарлах» → «тайлбарл», «зохиох» → «зохи».

    Монгол үйл үг нөхцөлтэй ирдэг (тайлбарлана, зохиож, ашигласан) тул үгийн эхлэлээр тааруулна.
    """
    return verb[:-2] if len(verb) > 4 else verb


def _matches(token: str, stem: str) -> bool:
    if not token.startswith(stem):
        return False
    rest = token[len(stem):]
    return not rest.startswith(_NOUN_SUFFIXES)


@dataclass(frozen=True)
class BloomResult:
    """Түвшин ба түүний үндэслэл (ФШ-11)."""
    level: int
    source: str                    # "verb" — тольд таарсан, "classifier" — ангилагч
    matched_verb: str | None = None
    confidence: float = 1.0

    @property
    def reason(self) -> str:
        if self.source == "verb":
            return f"Үйл үг: «{self.matched_verb}»"
        return f"Ангилагч: итгэл {self.confidence:.2f}"


class BloomDictionary:
    """Control: БлумынТоль. verbs: {"тайлбарлах": 2, ...} — bloom_verbs хүснэгтээс."""

    def __init__(self, verbs: dict[str, int]):
        self.verbs = {normalize(v): int(lvl) for v, lvl in verbs.items() if v and 1 <= int(lvl) <= 6}
        # Олон үгтэй хэллэг (жишээ гаргах) болон нэг үг
        self._phrases = {v: lvl for v, lvl in self.verbs.items() if " " in v}
        self._single = {verb_stem(v): (v, lvl) for v, lvl in self.verbs.items() if " " not in v}

    def extract_verbs(self, text: str) -> list[tuple[str, int]]:
        """үйлҮгЯлгах(): текстэд байгаа толийн үйл үгс ба түвшин (давталтгүй, илэрсэн дарааллаар)."""
        norm = normalize(text)
        found: dict[str, int] = {}
        for phrase, lvl in self._phrases.items():
            first, *rest = phrase.split()
            stem = verb_stem(rest[-1]) if rest else first
            if first in norm and stem in norm:
                found[phrase] = lvl
        for tok in tokens(text):
            for stem, (verb, lvl) in self._single.items():
                if _matches(tok, stem):
                    found.setdefault(verb, lvl)
        return list(found.items())

    def detect(self, text: str) -> BloomResult | None:
        """түвшинТаних(): таарсан хамгийн өндөр түвшин; таарахгүй бол None."""
        found = self.extract_verbs(text)
        if not found:
            return None
        verb, lvl = max(found, key=lambda x: x[1])
        return BloomResult(level=lvl, source="verb", matched_verb=verb)


def level_from_verbs(text: str, verbs: dict[str, int]) -> int | None:
    """Толиос таарсан хамгийн өндөр түвшинг буцаана; таарахгүй бол None."""
    r = BloomDictionary(verbs).detect(text)
    return r.level if r else None


def assess(text: str, dictionary: BloomDictionary, classifier=None) -> BloomResult | None:
    """блумТүвшинТодорхойлох(): эхлээд толь, таарахгүй бол ангилагч (ФШ-11)."""
    r = dictionary.detect(text)
    if r is not None:
        return r
    if classifier is None:
        from app.services.bloom.classifier import BloomClassifier
        classifier = BloomClassifier()
    return classifier.classify(text)


def level_gap(assessment_level: int, clo_level: int) -> str:
    """Δ = L(үнэлгээ) − L(CLO): <0 доогуур, =0 нийцсэн, >0 дээгүүр."""
    d = assessment_level - clo_level
    return "below" if d < 0 else ("match" if d == 0 else "above")


def load_seed_verbs(path: Path = SEED_VERBS_FILE) -> dict[str, int]:
    """data/seed/bloom_verbs.csv — ӨС хоосон үед (тест, анхны асаалт) ашиглана."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return {r["verb"].strip(): int(r["level"]) for r in csv.DictReader(f) if r.get("verb")}


def load_dictionary(db) -> BloomDictionary:
    """bloom_verbs хүснэгтээс толь ачаална (админ UC11-ээр засна); хоосон бол seed файл."""
    from sqlalchemy import select

    from app.models import BloomVerb
    verbs = {v.verb: v.level for v in db.scalars(select(BloomVerb))}
    return BloomDictionary(verbs or load_seed_verbs())
