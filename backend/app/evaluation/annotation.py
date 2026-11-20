"""Тэмдэглэгээтэй өгөгдөл (алтан стандарт) бэлтгэх, нэгтгэх. Хариуцагч: Б (СА3, СА4). Заавар: docs/ANNOTATION.md

Файлууд (data/private/annotations/ — git-д орохгүй):
    links_annotator_A.csv, links_annotator_B.csv  → links_gold.csv    (СА3: CLO × сургалтын элемент)
    bloom_annotator_A.csv, bloom_annotator_B.csv  → bloom_gold.csv    (СА4: Блумын түвшин)

Мөр бүр `split` баганатай: `dev` — θ сонгоход, `test` — эцсийн үнэлгээнд (Бүлэг 1: босгыг хөгжүүлэлтийн
өгөгдөл дээр сонгоно). Хуваалт нь түлхүүрийн hash-аар тогтдог тул дахин гаргахад өөрчлөгдөхгүй.
"""
from __future__ import annotations

import csv
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

LINK_LABELS = ("direct", "partial", "none")
BLOOM_LABELS = ("1", "2", "3", "4", "5", "6")
ASSESSMENT_TYPES = ("lab", "assignment", "exam")

LINK_COLUMNS = ["pair_id", "split", "course", "clo_id", "clo_code", "clo_text",
                "item_id", "item_type", "item_title", "item_text", "label", "note"]
BLOOM_COLUMNS = ["obj_id", "split", "course", "kind", "code", "text", "level", "note"]


class AnnotationError(ValueError):
    """Тэмдэглэгээний файлын алдаа (мөрийн дугаартай)."""


def split_of(key: str, dev_ratio: float) -> str:
    """Тогтвортой хуваалт: түлхүүрийн md5 → [0, 1)."""
    h = int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "dev" if h < dev_ratio else "test"


# --------------------------------------------------------------------------- Файл унших, бичих
def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:     # utf-8-sig: Excel-д зөв нээгдэнэ
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in r.items() if k is not None} for r in csv.DictReader(f)]


def _norm_link(v: str) -> str:
    v = v.strip().lower()
    return {"d": "direct", "шууд": "direct", "p": "partial", "хэсэгчлэн": "partial",
            "n": "none", "-": "none", "0": "none", "холбоогүй": "none"}.get(v, v)


def read_annotations(path: Path, task: str, allow_empty: bool = False) -> dict[str, dict]:
    """Тэмдэглэгээг уншиж шалгана: {id: мөр}. Буруу утгыг (мөрийн дугаар, шалтгаан)-аар мэдэгдэнэ."""
    id_col, lab_col, labels = (("pair_id", "label", LINK_LABELS) if task == "links"
                               else ("obj_id", "level", BLOOM_LABELS))
    rows, errors, out = read_csv(path), [], {}
    for n, r in enumerate(rows, start=2):
        if id_col not in r:
            raise AnnotationError(f"{path.name}: «{id_col}» багана алга")
        v = _norm_link(r.get(lab_col, "")) if task == "links" else r.get(lab_col, "").strip()
        if not v and not allow_empty:
            errors.append(f"мөр {n}: «{lab_col}» хоосон")
        elif v and v not in labels:
            errors.append(f"мөр {n}: «{r.get(lab_col)}» буруу (зөвшөөрөгдөх: {', '.join(labels)})")
        if r[id_col] in out:
            errors.append(f"мөр {n}: {r[id_col]} давхардсан")
        r[lab_col] = v
        out[r[id_col]] = r
    if errors:
        raise AnnotationError(f"{path.name}: " + "; ".join(errors[:20]) + (" …" if len(errors) > 20 else ""))
    return out


# --------------------------------------------------------------------------- Системээс загвар гаргах
@dataclass
class ExportResult:
    links: int
    bloom: int
    files: list[Path]


def export_templates(db, course_codes: list[str], out_dir: Path, dev_ratio: float = 0.3,
                     annotators: tuple[str, ...] = ("A", "B"), seed: int = 2026) -> ExportResult:
    """Сонгосон хичээлүүдийн ИДЭВХТЭЙ хувилбараас хоосон тэмдэглэх файл гаргана.

    Системийн санал, оноо, Блумын түвшин файлд ОРОХГҮЙ — тэмдэглэгч түүнд хөтлөгдөхгүй байх ёстой.
    Тэмдэглэгч бүрийн файл өөр дараалалтай (дарааллын нөлөөг багасгана).
    """
    from sqlalchemy import select

    from app.models import Clo, Course, LearningItem
    from app.services.analysis.course import item_text
    from app.services.versioning import active_version

    link_rows: list[dict] = []
    bloom_rows: list[dict] = []
    for code in course_codes:
        course = db.scalar(select(Course).where(Course.code == code))
        if course is None:
            raise AnnotationError(f"{code} кодтой хичээл олдсонгүй")
        v = active_version(db, course.id)
        if v is None:
            raise AnnotationError(f"{code}: идэвхтэй хувилбар алга")
        clos = list(db.scalars(select(Clo).where(Clo.version_id == v.id).order_by(Clo.code)))
        items = list(db.scalars(select(LearningItem).where(LearningItem.version_id == v.id).order_by(LearningItem.id)))
        if not clos or not items:
            raise AnnotationError(f"{code}: CLO эсвэл сургалтын элемент алга")
        for c in clos:
            key = f"{code}|{c.code}"
            bloom_rows.append({"obj_id": f"clo:{c.id}", "split": split_of(key, dev_ratio), "course": code,
                               "kind": "clo", "code": c.code, "text": c.text, "level": "", "note": ""})
            for it in items:
                pkey = f"{code}|{c.code}|{it.type}|{it.title}"
                link_rows.append({"pair_id": f"{c.id}-{it.id}", "split": split_of(pkey, dev_ratio), "course": code,
                                  "clo_id": c.id, "clo_code": c.code, "clo_text": c.text, "item_id": it.id,
                                  "item_type": it.type, "item_title": it.title,
                                  "item_text": item_text(it), "label": "", "note": ""})
        for it in items:
            if it.type in ASSESSMENT_TYPES:          # лекцийн түвшин зөрүүнд оролцохгүй (ФШ-12)
                key = f"{code}|{it.type}|{it.title}"
                bloom_rows.append({"obj_id": f"item:{it.id}", "split": split_of(key, dev_ratio), "course": code,
                                   "kind": it.type, "code": it.title, "text": item_text(it), "level": "", "note": ""})

    files = []
    for i, who in enumerate(annotators):
        rnd = random.Random(seed + i)
        lr, br = link_rows[:], bloom_rows[:]
        rnd.shuffle(lr)
        rnd.shuffle(br)
        for name, cols, rows in (("links", LINK_COLUMNS, lr), ("bloom", BLOOM_COLUMNS, br)):
            p = out_dir / f"{name}_annotator_{who}.csv"
            if p.exists():
                raise AnnotationError(f"{p} аль хэдийн байна — тэмдэглэгээ дарагдахгүйн тулд устгаж эсвэл өөр хавтас сонгоно уу")
            write_csv(p, cols, rows)
            files.append(p)
    return ExportResult(links=len(link_rows), bloom=len(bloom_rows), files=files)


# --------------------------------------------------------------------------- Хоёр тэмдэглэгээг нэгтгэх
def merge(path_a: Path, path_b: Path, task: str, out: Path) -> dict:
    """gold.csv үүсгэнэ: санал нийлсэн мөр шууд, зөрүүтэйг `disputed=1`, хоосон шошготой үлдээж хэлэлцүүлнэ.

    Хэлэлцсэний дараа gold.csv-ийн хоосон шошгыг гараар бөглөнө. Дахин merge хийхэд өмнө бөглөсөн
    шошгыг хадгална (out файл байвал).
    """
    from app.evaluation.metrics import cohen_kappa

    a, b = read_annotations(path_a, task), read_annotations(path_b, task)
    if a.keys() != b.keys():
        only = sorted(a.keys() ^ b.keys())[:5]
        raise AnnotationError(f"Хоёр файлын мөрүүд зөрүүтэй (жишээ: {', '.join(only)})")
    id_col, lab_col, cols = (("pair_id", "label", LINK_COLUMNS) if task == "links"
                             else ("obj_id", "level", BLOOM_COLUMNS))
    previous = read_annotations(out, task, allow_empty=True) if out.exists() else {}
    rows, disputed = [], 0
    for k in sorted(a):
        r = dict(a[k])
        la, lb = a[k][lab_col], b[k][lab_col]
        r[f"{lab_col}_A"], r[f"{lab_col}_B"] = la, lb
        r["note"] = " | ".join(x for x in (a[k].get("note"), b[k].get("note")) if x)
        if la == lb:
            r[lab_col], r["disputed"] = la, "0"
        else:
            disputed += 1
            r[lab_col], r["disputed"] = previous.get(k, {}).get(lab_col, ""), "1"
        rows.append(r)
    write_csv(out, cols[:-2] + [f"{lab_col}_A", f"{lab_col}_B", "disputed", lab_col, "note"], rows)
    keys = sorted(a)
    return {"rows": len(rows), "disputed": disputed,
            "kappa": cohen_kappa([a[k][lab_col] for k in keys], [b[k][lab_col] for k in keys])}
