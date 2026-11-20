"""Блумын түвшин (ФШ-11, ФШ-12). Control: БлумынТоль, ХичээлийнШинжилгээ. Хариуцагч: Б4, Б5."""
from app.services.nlp.preprocess import tokens

LEVELS = {1: "санах", 2: "ойлгох", 3: "хэрэглэх", 4: "шинжлэх", 5: "үнэлэх", 6: "бүтээх"}


def level_from_verbs(text: str, verbs: dict[str, int]) -> int | None:
    """Толиос таарсан хамгийн өндөр түвшинг буцаана; таарахгүй бол None (→ ангилагч, TODO Б4).

    verbs: {"тайлбарлах": 2, ...}  (bloom_verbs хүснэгт)
    Монгол үйл үг нөхцөлтэй ирдэг тул үгийн эхлэлээр (stem) тааруулна.
    """
    found = [lvl for w in tokens(text) for v, lvl in verbs.items() if w.startswith(v[:-2] if len(v) > 4 else v)]
    return max(found) if found else None


def level_gap(assessment_level: int, clo_level: int) -> str:
    """Δ = L(үнэлгээ) − L(CLO): <0 доогуур, =0 нийцсэн, >0 дээгүүр."""
    d = assessment_level - clo_level
    return "below" if d < 0 else ("match" if d == 0 else "above")
