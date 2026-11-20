"""CSV импортын нийтлэг логик (ФШ-06, ФШ-08, ФБШ-05). Зураг: өгөгдөл импортлох үйл ажиллагаа.

Хариуцагч: CLO/элемент — Б2, ажлын зарлал — А7. Баганын тодорхойлолт: docs/DATA.md.
"""
import csv
import io
import re
from dataclasses import dataclass, field

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(\+?976[\s-]?)?\b\d{4}[\s-]?\d{4}\b")


@dataclass
class ImportResult:
    rows: list[dict] = field(default_factory=list)
    errors: list[tuple[int, str]] = field(default_factory=list)   # (мөрийн дугаар, шалтгаан)


def parse_csv(content: str, required: list[str]) -> ImportResult:
    reader = csv.DictReader(io.StringIO(content))
    missing = [c for c in required if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"Дутуу багана: {', '.join(missing)}")
    res, seen = ImportResult(), set()
    for i, row in enumerate(reader, start=2):          # 1-р мөр = толгой
        empty = [c for c in required if not (row.get(c) or "").strip()]
        if empty:
            res.errors.append((i, f"Хоосон талбар: {', '.join(empty)}"))
            continue
        key = tuple((row[c] or "").strip().lower() for c in required)
        if key in seen:
            res.errors.append((i, "Давхардсан мөр"))
            continue
        seen.add(key)
        res.rows.append({k: (v or "").strip() for k, v in row.items()})
    return res


def remove_pii(text: str) -> str:
    """Имэйл, утасны дугаарыг арилгана. TODO(А7): хүний нэр илрүүлэх."""
    return PHONE.sub("[утас]", EMAIL.sub("[имэйл]", text))
