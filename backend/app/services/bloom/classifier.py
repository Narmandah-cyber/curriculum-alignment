"""Блумын түвшний ангилагч (ФШ-11). Хариуцагч: Б4.

Толинд үйл үг таарахгүй үед (жишээ нь «Primary key гэж юу вэ?» гэх мэт асуулт) хэрэглэнэ.
Түвшин бүрийн жишээ өгүүлбэрүүдийн тэмдэгтийн 3-грамын төвтэй (centroid) косинусаар харьцуулж,
хамгийн ойрын түвшин ба итгэлийн оноог буцаана. Гадны сан шаардахгүй, детерминист (ФБШ-07).

Жишээнүүдийг тэмдэглэгээтэй өгөгдөл (СА4, docs/DATA.md) бэлэн болмогц түүгээр сольж/өргөтгөнө.
"""
from __future__ import annotations

import math
from collections import Counter

from app.services.bloom.levels import BloomResult
from app.services.nlp.preprocess import normalize

# Түвшин бүрийн асуулт, даалгаврын төлөөлөх хэллэгүүд (монгол + англи)
EXEMPLARS: dict[int, list[str]] = {
    1: ["гэж юу вэ", "юу гэж нэрлэдэг вэ", "хэзээ", "хэн", "нэр нь юу вэ", "тодорхойлолтыг бич",
        "жагсаан бич", "what is", "define", "list", "name the", "ирц", "тест сонгох"],
    2: ["яагаад", "ялгааг тайлбарла", "өөрийн үгээр", "хураангуйлж бич", "жишээгээр тайлбарла",
        "explain", "describe", "summarize", "ойлголт", "үндсэн ойлголт", "танилцуулга"],
    3: ["тооцоол", "бодлого бод", "кодыг бич", "хэрэгжүүл", "ашиглан хийх", "хүснэгт үүсгэх", "query бичих",
        "solve", "implement", "use", "apply", "дасгал", "лаборатори ажил", "sql хүсэлт"],
    4: ["харьцуул", "задлан шинжил", "шалтгааныг тодорхойл", "ялгаж ангил", "хэвийн хэлбэрт оруул",
        "analyze", "compare", "normalize", "debug", "алдааг ол", "бүтцийг задал"],
    5: ["үнэлж дүгнэ", "сайн муу талыг", "аль нь илүү", "сонголтоо үндэслэ", "шүүмжлэлтэй",
        "evaluate", "justify", "assess", "critique", "шийдлийг үнэл", "тохирохыг сонго"],
    6: ["зохиомжил", "төсөл боловсруул", "шинээр бүтээ", "загвар зохио", "систем хөгжүүл", "төлөвлөгөө гарга",
        "design", "create", "develop", "build", "бие даалтын төсөл", "прототип хий"],
}


def _ngrams(text: str, n: int = 3) -> Counter:
    t = f" {normalize(text)} "
    return Counter(t[i:i + n] for i in range(max(len(t) - n + 1, 0)))


def _cos(a: Counter, b: Counter) -> float:
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


class BloomClassifier:
    """Тэмдэгтийн n-грамын төвд суурилсан хялбар ангилагч."""

    def __init__(self, exemplars: dict[int, list[str]] | None = None, default_level: int = 1):
        self.default_level = default_level
        self.centroids: dict[int, Counter] = {}
        for lvl, phrases in (exemplars or EXEMPLARS).items():
            c: Counter = Counter()
            for p in phrases:
                c.update(_ngrams(p))
            self.centroids[lvl] = c

    def scores(self, text: str) -> dict[int, float]:
        g = _ngrams(text)
        return {lvl: _cos(g, c) for lvl, c in self.centroids.items()}

    def classify(self, text: str) -> BloomResult:
        """Хамгийн өндөр оноотой түвшин; итгэл = тухайн онооны бусдаас харьцангуй давуу байдал."""
        sc = self.scores(text)
        total = sum(sc.values())
        if total == 0:
            return BloomResult(level=self.default_level, source="classifier", confidence=0.0)
        lvl = max(sorted(sc), key=lambda k: sc[k])      # тэнцвэл доод түвшин (детерминист)
        return BloomResult(level=lvl, source="classifier", confidence=round(sc[lvl] / total, 2))
