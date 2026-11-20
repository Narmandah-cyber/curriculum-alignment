"""Хичээлийн хувилбар (ФШ-07, UC12). Control: ХичээлийнХувилбар. Хариуцагч: Б3.

Бүлэг 2, Зураг: хувилбар шинэчлэх үйл ажиллагаа.

    renew              ↔ Хичээл.хөтөлбөрШинэчлэх(хичээлийнЖил)
    _copy              ↔ ХичээлийнХувилбар.хуулах()
    _to_history        ↔ ХичээлийнХувилбар.түүхэндШилжүүлэх()
    (status="active")  ↔ ХичээлийнХувилбар.идэвхжүүлэх()
    is_editable        ↔ ХичээлийнХувилбар.засахБоломжтойЭсэх()
    compare            ↔ ХичээлийнХувилбар.ялгааТооцох()

Бүх алхам нэг гүйлгээнд хийгдэнэ: алдаа гарвал rollback хийх тул хичээл идэвхтэй хувилбаргүй
эсвэл хоёр идэвхтэй хувилбартай болохгүй.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Clo, CourseVersion, LearningItem, Link

ACTIVE, HISTORY = "active", "history"


class VersionError(Exception):
    """Хувилбарын дүрэм зөрчигдсөн (HTTP 409)."""


def is_editable(version: CourseVersion) -> bool:
    """засахБоломжтойЭсэх(): «түүх» хувилбарыг засахгүй."""
    return version.status == ACTIVE


def active_version(db: Session, course_id: int) -> CourseVersion | None:
    """идэвхтэйХувилбарАвах()."""
    return db.scalar(select(CourseVersion).where(CourseVersion.course_id == course_id,
                                                 CourseVersion.status == ACTIVE))


def renew(db: Session, course_id: int, academic_year: str) -> CourseVersion:
    """хөтөлбөрШинэчлэх(): хуулах → баталгаажсан холбоос шилжүүлэх → түүхэндШилжүүлэх → идэвхжүүлэх."""
    academic_year = academic_year.replace("–", "-")
    exists = db.scalar(select(CourseVersion).where(CourseVersion.course_id == course_id,
                                                   CourseVersion.academic_year == academic_year))
    if exists:
        raise VersionError(f"{academic_year} оны хувилбар аль хэдийн байна")
    old = active_version(db, course_id)
    if old is None:
        raise VersionError("Идэвхтэй хувилбар олдсонгүй")
    try:
        last_no = db.scalar(select(func.max(CourseVersion.version_no))
                            .where(CourseVersion.course_id == course_id)) or 0
        new = CourseVersion(course_id=course_id, version_no=last_no + 1, academic_year=academic_year,
                            status=ACTIVE, previous_version_id=old.id)
        old.status = HISTORY                      # түүхэндШилжүүлэх()
        db.flush()                                # нэг идэвхтэй хувилбар
        db.add(new)
        db.flush()
        _copy(db, old, new)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return new


def _copy(db: Session, old: CourseVersion, new: CourseVersion) -> None:
    """хуулах(): CLO, элемент, баталгаажсан CLO–элемент ба CLO–PLO холбоосыг шинэ хувилбарт хуулна."""
    clo_map: dict[int, int] = {}
    for c in db.scalars(select(Clo).where(Clo.version_id == old.id)):
        n = Clo(version_id=new.id, code=c.code, text=c.text, bloom_level=c.bloom_level,
                level_source=c.level_source)
        db.add(n)
        db.flush()
        clo_map[c.id] = n.id
    item_map: dict[int, int] = {}
    for i in db.scalars(select(LearningItem).where(LearningItem.version_id == old.id)):
        n = LearningItem(version_id=new.id, type=i.type, title=i.title, text=i.text,
                         question_text=i.question_text, bloom_level=i.bloom_level, level_source=i.level_source)
        db.add(n)
        db.flush()
        item_map[i.id] = n.id
    if not clo_map:
        return
    confirmed = db.scalars(select(Link).where(Link.source_type == "clo", Link.target_type.in_(("item", "plo")),
                                              Link.status == "confirmed",
                                              Link.source_id.in_(list(clo_map))))
    for lk in confirmed:
        if lk.target_type == "item":
            if lk.target_id not in item_map:
                continue
            target = item_map[lk.target_id]
        else:
            target = lk.target_id               # PLO нь хөтөлбөрийнх, хувилбараар хуулагдахгүй (ФШ-14)
        db.add(Link(run_id=None, source_type="clo", source_id=clo_map[lk.source_id], target_type=lk.target_type,
                    target_id=target, strength=lk.strength, score=lk.score, method=lk.method,
                    level_gap=lk.level_gap, status="confirmed", llm_explanation=lk.llm_explanation))


def compare(db: Session, v1: CourseVersion, v2: CourseVersion) -> list[dict]:
    """ялгааТооцох(): CLO-г кодоор, элементийг (төрөл, гарчиг)-аар тааруулж нэмэгдсэн/өөрчлөгдсөн/хасагдсан."""
    changes: list[dict] = []

    def diff(kind: str, old: dict[str, str], new: dict[str, str]) -> None:
        for key in sorted(new.keys() - old.keys()):
            changes.append({"change": "added", "kind": kind, "key": key, "new_text": new[key]})
        for key in sorted(old.keys() & new.keys()):
            if old[key].strip() != new[key].strip():
                changes.append({"change": "modified", "kind": kind, "key": key,
                                "old_text": old[key], "new_text": new[key]})
        for key in sorted(old.keys() - new.keys()):
            changes.append({"change": "removed", "kind": kind, "key": key, "old_text": old[key]})

    def clos(v: CourseVersion) -> dict[str, str]:
        return {c.code: c.text for c in db.scalars(select(Clo).where(Clo.version_id == v.id))}

    def items(v: CourseVersion) -> dict[str, str]:
        return {i.title: (i.text or "") + (f" | {i.question_text}" if i.question_text else "")
                for i in db.scalars(select(LearningItem).where(LearningItem.version_id == v.id))}

    diff("clo", clos(v1), clos(v2))
    diff("item", items(v1), items(v2))
    order = {"added": 0, "modified": 1, "removed": 2}
    return sorted(changes, key=lambda c: (order[c["change"]], c["kind"], c["key"]))
