"""Сэдвийн ижил төстэй байдал (ФШ-10, ФШ-17). Хариуцагч: А6.

    s = λ · s_emb + (1 − λ) · s_rule   (Бүлэг 2, Зураг: хичээлийн шинжилгээний үйл ажиллагаа)
"""
import math
from collections.abc import Sequence

from app.services.nlp.preprocess import tokens


def cosine(u: Sequence[float], v: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(u, v, strict=True))
    nu, nv = math.sqrt(sum(a * a for a in u)), math.sqrt(sum(b * b for b in v))
    return 0.0 if nu == 0 or nv == 0 else dot / (nu * nv)


def keyword_score(a: str, b: str) -> float:
    """Дүрэмд суурилсан оноо: түлхүүр үгийн давхцал (Jaccard). TODO(А6): стоп үг, үгийн үндэс."""
    ta, tb = set(tokens(a)), set(tokens(b))
    return 0.0 if not ta or not tb else len(ta & tb) / len(ta | tb)


def hybrid_score(s_emb: float, s_rule: float, lam: float) -> float:
    return lam * s_emb + (1 - lam) * s_rule


class Embedder:
    """Embedding загварын хэрэглэгч. TODO(А6): sentence-transformers-оор хэрэгжүүлж, кэш хийх."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def encode(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("А6: embedding загвар холбох")
