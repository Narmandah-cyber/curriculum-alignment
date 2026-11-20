"""Текст цэвэрлэх, хэвийн болгох (ФШ-10, ФШ-15). Control: ХичээлийнШинжилгээ.текстБэлтгэх(). Хариуцагч: А6."""
import re
import unicodedata

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s\-+#./]", re.UNICODE)


def normalize(text: str) -> str:
    """Unicode NFC, жижиг үсэг, илүүдэл тэмдэгт ба хоосон зайг цэвэрлэнэ."""
    text = unicodedata.normalize("NFC", text or "")
    text = text.lower()
    text = _PUNCT.sub(" ", text)
    return _WS.sub(" ", text).strip()


def tokens(text: str) -> list[str]:
    return normalize(text).split()
