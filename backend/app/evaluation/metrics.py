"""Үнэлгээний хэмжүүрүүд (Бүлэг 1: Precision, Recall, F1, macro-F1, Cohen's kappa). Хариуцагч: Б (СА3, СА4).

Гадны сан (scikit-learn) шаардахгүй, детерминист. Томьёо:
    P = TP / (TP + FP),  R = TP / (TP + FN),  F1 = 2PR / (P + R)
    macro-F1 = ангилал бүрийн F1-ийн энгийн дундаж
    κ = (p_o − p_e) / (1 − p_e)                                   (Cohen, 1960)
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class PRF:
    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


def prf(gold: Sequence[bool], pred: Sequence[bool]) -> PRF:
    """Хоёртын ангилал (холбоотой / холбоогүй)."""
    _same_len(gold, pred)
    tp = sum(1 for g, p in zip(gold, pred, strict=False) if g and p)
    fp = sum(1 for g, p in zip(gold, pred, strict=False) if not g and p)
    fn = sum(1 for g, p in zip(gold, pred, strict=False) if g and not p)
    return PRF(tp, fp, fn)


def cohen_kappa(a: Sequence[Hashable], b: Sequence[Hashable]) -> float:
    """Хоёр тэмдэглэгчийн (эсвэл систем–мэргэжилтний) тохироо. Бүх тэмдэглэгээ нэг ангилалд бол 1.0."""
    _same_len(a, b)
    n = len(a)
    if n == 0:
        return 0.0
    p_o = sum(1 for x, y in zip(a, b, strict=False) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    p_e = sum(ca[k] * cb[k] for k in ca.keys() | cb.keys()) / (n * n)
    if p_e == 1.0:
        return 1.0
    return (p_o - p_e) / (1 - p_e)


def confusion(gold: Sequence[Hashable], pred: Sequence[Hashable], labels: Sequence[Hashable]) -> list[list[int]]:
    """Мөр = жинхэнэ ангилал, багана = таамагласан ангилал."""
    _same_len(gold, pred)
    idx = {lab: i for i, lab in enumerate(labels)}
    m = [[0] * len(labels) for _ in labels]
    for g, p in zip(gold, pred, strict=False):
        if g in idx and p in idx:
            m[idx[g]][idx[p]] += 1
    return m


def per_class_f1(gold: Sequence[Hashable], pred: Sequence[Hashable], labels: Sequence[Hashable]) -> dict:
    return {lab: prf([g == lab for g in gold], [p == lab for p in pred]).f1 for lab in labels}


def macro_f1(gold: Sequence[Hashable], pred: Sequence[Hashable], labels: Sequence[Hashable] | None = None) -> float:
    """Ангилал бүрийн F1-ийн дундаж. labels өгөөгүй бол gold-д байгаа ангиллууд."""
    labs = list(labels) if labels is not None else sorted(set(gold), key=str)
    if not labs:
        return 0.0
    f = per_class_f1(gold, pred, labs)
    return sum(f.values()) / len(labs)


def accuracy(gold: Sequence[Hashable], pred: Sequence[Hashable]) -> float:
    _same_len(gold, pred)
    return sum(1 for g, p in zip(gold, pred, strict=False) if g == p) / len(gold) if gold else 0.0


def threshold_curve(scores: Sequence[float], gold: Sequence[bool], thresholds: Sequence[float]) -> list[dict]:
    """θ бүрд P, R, F1 (P–R муруй, Бүлэг 4-ийн зураг)."""
    rows = []
    for t in thresholds:
        r = prf(gold, [s >= t for s in scores])
        rows.append({"threshold": round(t, 4), "precision": r.precision, "recall": r.recall, "f1": r.f1,
                     "tp": r.tp, "fp": r.fp, "fn": r.fn})
    return rows


def best_threshold(scores: Sequence[float], gold: Sequence[bool], thresholds: Sequence[float]) -> dict:
    """Хөгжүүлэлтийн өгөгдөл дээр F1-ийг хамгийн их болгох θ. Тэнцвэл өндөр P-тэй (дараа нь бага θ)-г сонгоно."""
    curve = threshold_curve(scores, gold, thresholds)
    return max(curve, key=lambda r: (round(r["f1"], 10), round(r["precision"], 10), -r["threshold"]))


def landis_koch(k: float) -> str:
    """Kappa-гийн тайлбар (Landis & Koch, 1977)."""
    if k < 0:
        return "тохироогүй"
    for bound, name in ((0.20, "бага"), (0.40, "сул"), (0.60, "дунд зэрэг"), (0.80, "нэлээд")):
        if k <= bound:
            return name
    return "бараг төгс"


def grid(start: float = 0.05, stop: float = 0.95, step: float = 0.05) -> list[float]:
    n = int(round((stop - start) / step)) + 1
    return [round(start + i * step, 4) for i in range(n)]


def _same_len(a: Sequence, b: Sequence) -> None:
    if len(a) != len(b):
        raise ValueError(f"Урт зөрүүтэй: {len(a)} ба {len(b)}")
