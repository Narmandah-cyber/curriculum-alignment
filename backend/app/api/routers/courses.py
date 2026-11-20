"""UC2 Хичээлийн өгөгдөл бүртгэх, UC12 Хичээлийн хөтөлбөр шинэчлэх (ФШ-04..07, 11, 21). Хариуцагч: Б2, Б3.

Control: Хичээл, ХичээлийнХувилбар, CLO, СургалтынЭлемент.
Эрх (ФБШ-04): хичээлийг зөвхөн тухайн хичээлийн багш засна; хөтөлбөрийн хариуцагч, админ харж болно.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_role, user_roles
from app.db.session import get_db
from app.models import AnalysisRun, Clo, Course, CourseVersion, LearningItem, Link, Report, User
from app.schemas import (
    CloIn,
    CloOut,
    CloUpdate,
    CourseIn,
    CourseOut,
    CourseSummary,
    CourseUpdate,
    ImportOut,
    ImportRowError,
    ItemIn,
    ItemOut,
    ItemUpdate,
    RenewIn,
    VersionCompareOut,
    VersionOut,
)
from app.services import versioning
from app.services.analysis.course import item_text, summary
from app.services.bloom.classifier import BloomClassifier
from app.services.bloom.levels import BloomDictionary, assess, load_dictionary
from app.services.importers.csv_import import parse_csv

router = APIRouter(prefix="/api", tags=["courses"])

ITEM_TYPES = ("lecture", "lab", "assignment", "exam")
VIEW_ROLES = {"coordinator", "admin"}
FORBIDDEN = "Танд энэ үйлдлийг хийх эрх байхгүй"
_classifier = BloomClassifier()


# --------------------------------------------------------------------------- туслах функцууд
def _course_or_404(db: Session, course_id: int) -> Course:
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(404, "Хичээл олдсонгүй")
    return c


def _version_or_404(db: Session, version_id: int) -> CourseVersion:
    v = db.get(CourseVersion, version_id)
    if not v:
        raise HTTPException(404, "Хувилбар олдсонгүй")
    return v


def can_view(db: Session, user: User, course: Course) -> bool:
    return course.teacher_id == user.id or bool(VIEW_ROLES & set(user_roles(db, user.id)))


def check_view(db: Session, user: User, course: Course) -> None:
    if not can_view(db, user, course):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN)


def check_owner(user: User, course: Course) -> None:
    """эрхтэйЭсэх(): багш зөвхөн өөрийн хичээлийг засна (ФБШ-04)."""
    if course.teacher_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN)


def check_editable(version: CourseVersion) -> None:
    """засахБоломжтойЭсэх(): «түүх» хувилбарыг засахгүй (409)."""
    if not versioning.is_editable(version):
        raise HTTPException(status.HTTP_409_CONFLICT, "Түүх хувилбарыг засах боломжгүй")


def version_out(db: Session, v: CourseVersion) -> VersionOut:
    out = VersionOut.model_validate(v)
    out.clo_count = db.scalar(select(func.count(Clo.id)).where(Clo.version_id == v.id)) or 0
    out.item_count = db.scalar(select(func.count(LearningItem.id)).where(LearningItem.version_id == v.id)) or 0
    return out


def course_out(db: Session, c: Course) -> CourseOut:
    out = CourseOut.model_validate(c)
    v = versioning.active_version(db, c.id)
    if v:
        out.active_version = version_out(db, v)
        out.summary = CourseSummary(**summary(db, v.id))
    return out


def _reason(obj, dictionary: BloomDictionary, text: str) -> str | None:
    """Түвшний үндэслэл (ФШ-11)."""
    if obj.bloom_level is None:
        return None
    if obj.level_source == "manual":
        return "Гараар зассан"
    r = assess(text, dictionary, _classifier)
    return r.reason if r and r.level == obj.bloom_level else None


def clo_out(c: Clo, dictionary: BloomDictionary) -> CloOut:
    out = CloOut.model_validate(c)
    out.level_reason = _reason(c, dictionary, c.text)
    return out


def item_out(i: LearningItem, dictionary: BloomDictionary) -> ItemOut:
    out = ItemOut.model_validate(i)
    out.level_reason = _reason(i, dictionary, item_text(i))
    return out


def _auto_level(obj, text: str, dictionary: BloomDictionary) -> None:
    """блумТүвшинОноох(): гараар зассан түвшинг хөндөхгүй."""
    if obj.level_source == "manual":
        return
    r = assess(text, dictionary, _classifier)
    obj.bloom_level, obj.level_source = (r.level, "auto") if r else (None, None)


def _set_manual(obj, level: int | None) -> None:
    """блумТүвшинЗасах() (ФШ-21). None өгвөл автомат руу буцна."""
    obj.bloom_level, obj.level_source = (level, "manual") if level else (None, None)


def _commit(db: Session, conflict_msg: str) -> None:
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, conflict_msg) from e


# --------------------------------------------------------------------------- Хичээл (Б2)
@router.get("/courses", response_model=list[CourseOut])
def list_courses(mine: bool = True, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Хянах самбар: багшийн хичээлүүд. mine=false — хөтөлбөрийн хариуцагч, админ бүх хичээлийг харна."""
    q = select(Course).order_by(Course.code)
    if mine or not (VIEW_ROLES & set(user_roles(db, user.id))):
        q = q.where(Course.teacher_id == user.id)
    return [course_out(db, c) for c in db.scalars(q)]


@router.post("/courses", response_model=CourseOut, status_code=201)
def create_course(body: CourseIn, db: Session = Depends(get_db), user: User = Depends(require_role("teacher"))):
    """Хичээл.үүсгэх() + анхны идэвхтэй хувилбар (v1)."""
    c = Course(code=body.code.strip(), name=body.name.strip(), credits=body.credits, teacher_id=user.id)
    db.add(c)
    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(409, f"{body.code} кодтой хичээл бүртгэлтэй байна") from e
    db.add(CourseVersion(course_id=c.id, version_no=1, academic_year=body.academic_year.replace("–", "-"),
                         status=versioning.ACTIVE))
    db.commit()
    return course_out(db, c)


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = _course_or_404(db, course_id)
    check_view(db, user, c)
    return course_out(db, c)


@router.patch("/courses/{course_id}", response_model=CourseOut)
def update_course(course_id: int, body: CourseUpdate, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    """Хичээл.мэдээлэлЗасах()."""
    c = _course_or_404(db, course_id)
    check_owner(user, c)
    for k, v in body.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(c, k, v.strip() if isinstance(v, str) else v)
    _commit(db, "Хичээлийн код давхардсан")
    return course_out(db, c)


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Хичээл.устгах(): хувилбар, CLO, элемент, холбоос, шинжилгээг хамт устгана."""
    c = _course_or_404(db, course_id)
    check_owner(user, c)
    vids = list(db.scalars(select(CourseVersion.id).where(CourseVersion.course_id == c.id)))
    clo_ids = list(db.scalars(select(Clo.id).where(Clo.version_id.in_(vids))))
    if clo_ids:
        db.query(Link).filter(Link.source_type == "clo", Link.source_id.in_(clo_ids)).delete(False)
    for run in db.scalars(select(AnalysisRun).where(AnalysisRun.version_id.in_(vids))):
        db.query(Link).filter(Link.run_id == run.id).delete(False)
        db.query(Report).filter(Report.run_id == run.id).delete(False)
        db.delete(run)
    db.query(Clo).filter(Clo.version_id.in_(vids)).delete(False)
    db.query(LearningItem).filter(LearningItem.version_id.in_(vids)).delete(False)
    # previous_version_id-ийн гадаад түлхүүрээс болж шинээс нь хуучин руу устгана
    for v in sorted(db.scalars(select(CourseVersion).where(CourseVersion.id.in_(vids))),
                    key=lambda v: -v.version_no):
        db.delete(v)
        db.flush()
    db.delete(c)
    db.commit()


# --------------------------------------------------------------------------- Хувилбар (Б3)
@router.get("/courses/{course_id}/versions", response_model=list[VersionOut])
def list_versions(course_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """хувилбаруудАвах(): шинээс нь хуучин руу."""
    c = _course_or_404(db, course_id)
    check_view(db, user, c)
    vs = db.scalars(select(CourseVersion).where(CourseVersion.course_id == c.id)
                    .order_by(CourseVersion.version_no.desc()))
    return [version_out(db, v) for v in vs]


@router.post("/courses/{course_id}/versions", response_model=VersionOut, status_code=201)
def renew_course(course_id: int, body: RenewIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """хөтөлбөрШинэчлэх(хичээлийнЖил): хуулах → түүхэндШилжүүлэх → идэвхжүүлэх (ФШ-07)."""
    c = _course_or_404(db, course_id)
    check_owner(user, c)
    try:
        v = versioning.renew(db, c.id, body.academic_year)
    except versioning.VersionError as e:
        raise HTTPException(409, str(e)) from e
    return version_out(db, v)


@router.get("/versions/compare", response_model=VersionCompareOut)
def compare_versions(v1: int, v2: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """ялгааТооцох(): v1 (хуучин) → v2 (шинэ)."""
    a, b = _version_or_404(db, v1), _version_or_404(db, v2)
    if a.course_id != b.course_id:
        raise HTTPException(400, "Өөр хичээлийн хувилбаруудыг харьцуулах боломжгүй")
    check_view(db, user, _course_or_404(db, a.course_id))
    changes = versioning.compare(db, a, b)
    return VersionCompareOut(
        v1=version_out(db, a), v2=version_out(db, b), changes=changes,
        added=sum(c["change"] == "added" for c in changes),
        modified=sum(c["change"] == "modified" for c in changes),
        removed=sum(c["change"] == "removed" for c in changes),
    )


def _version_for_view(db: Session, user: User, version_id: int) -> CourseVersion:
    v = _version_or_404(db, version_id)
    check_view(db, user, _course_or_404(db, v.course_id))
    return v


def _version_for_edit(db: Session, user: User, version_id: int) -> CourseVersion:
    v = _version_or_404(db, version_id)
    check_owner(user, _course_or_404(db, v.course_id))
    check_editable(v)
    return v


# --------------------------------------------------------------------------- CLO (Б2, ФШ-04)
@router.get("/versions/{version_id}/clos", response_model=list[CloOut])
def list_clos(version_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """CLOжагсаалтАвах()."""
    _version_for_view(db, user, version_id)
    d = load_dictionary(db)
    return [clo_out(c, d) for c in db.scalars(select(Clo).where(Clo.version_id == version_id).order_by(Clo.code))]


@router.post("/versions/{version_id}/clos", response_model=CloOut, status_code=201)
def add_clo(version_id: int, body: CloIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """CLOНэмэх(): засахБоломжтойЭсэх() шалгана (түүх бол 409); Блумын түвшинг автоматаар ононо."""
    _version_for_edit(db, user, version_id)
    code = body.code.strip()
    if db.scalar(select(Clo.id).where(Clo.version_id == version_id, Clo.code == code)):
        raise HTTPException(409, f"{code} кодтой CLO бүртгэлтэй байна")
    c = Clo(version_id=version_id, code=code, text=body.text.strip())
    d = load_dictionary(db)
    if body.bloom_level:
        _set_manual(c, body.bloom_level)
    else:
        _auto_level(c, c.text, d)
    db.add(c)
    db.commit()
    return clo_out(c, d)


@router.patch("/clos/{clo_id}", response_model=CloOut)
def update_clo(clo_id: int, body: CloUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """текстЗасах(), блумТүвшинЗасах() (ФШ-21)."""
    c = db.get(Clo, clo_id) or _not_found("CLO")
    _version_for_edit(db, user, c.version_id)
    data = body.model_dump(exclude_unset=True)
    d = load_dictionary(db)
    if data.get("code"):
        code = data["code"].strip()
        if db.scalar(select(Clo.id).where(Clo.version_id == c.version_id, Clo.code == code, Clo.id != c.id)):
            raise HTTPException(409, f"{code} кодтой CLO бүртгэлтэй байна")
        c.code = code
    if data.get("text"):
        c.text = data["text"].strip()
        _auto_level(c, c.text, d)
    if "bloom_level" in data:
        _set_manual(c, data["bloom_level"])
        if data["bloom_level"] is None:
            _auto_level(c, c.text, d)
    db.commit()
    return clo_out(c, d)


@router.delete("/clos/{clo_id}", status_code=204)
def delete_clo(clo_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """CLOХасах(): холбоосуудыг хамт устгана."""
    c = db.get(Clo, clo_id) or _not_found("CLO")
    _version_for_edit(db, user, c.version_id)
    db.query(Link).filter(Link.source_type == "clo", Link.source_id == c.id).delete(False)
    db.delete(c)
    db.commit()


# --------------------------------------------------------------------------- Сургалтын элемент (Б2, ФШ-05)
@router.get("/versions/{version_id}/items", response_model=list[ItemOut])
def list_items(version_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """элементүүдАвах()."""
    _version_for_view(db, user, version_id)
    d = load_dictionary(db)
    q = select(LearningItem).where(LearningItem.version_id == version_id).order_by(LearningItem.id)
    return [item_out(i, d) for i in db.scalars(q)]


@router.post("/versions/{version_id}/items", response_model=ItemOut, status_code=201)
def add_item(version_id: int, body: ItemIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """элементНэмэх()."""
    _version_for_edit(db, user, version_id)
    i = LearningItem(version_id=version_id, type=body.type, title=body.title.strip(), text=(body.text or "").strip(),
                     question_text=(body.question_text or "").strip() or None)
    d = load_dictionary(db)
    if body.bloom_level:
        _set_manual(i, body.bloom_level)
    else:
        _auto_level(i, item_text(i), d)
    db.add(i)
    db.commit()
    return item_out(i, d)


@router.patch("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, body: ItemUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """текстЗасах(), блумТүвшинЗасах() (ФШ-21)."""
    i = db.get(LearningItem, item_id) or _not_found("Сургалтын элемент")
    _version_for_edit(db, user, i.version_id)
    data = body.model_dump(exclude_unset=True)
    d = load_dictionary(db)
    text_changed = False
    for k in ("type", "title", "text"):
        if data.get(k) is not None:
            setattr(i, k, data[k].strip())
            text_changed = True
    if "question_text" in data:
        i.question_text = (data["question_text"] or "").strip() or None
        text_changed = True
    if "bloom_level" in data:
        _set_manual(i, data["bloom_level"])
        if data["bloom_level"] is None:
            _auto_level(i, item_text(i), d)
    elif text_changed:
        _auto_level(i, item_text(i), d)
    db.commit()
    return item_out(i, d)


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """элементХасах()."""
    i = db.get(LearningItem, item_id) or _not_found("Сургалтын элемент")
    _version_for_edit(db, user, i.version_id)
    db.query(Link).filter(Link.target_type == "item", Link.target_id == i.id).delete(False)
    db.delete(i)
    db.commit()


# --------------------------------------------------------------------------- CSV импорт (Б2, ФШ-06)
@router.post("/versions/{version_id}/import", response_model=ImportOut)
async def import_csv(version_id: int, kind: str = Query(pattern="^(clo|item)$"), file: UploadFile = File(...),
                     db: Session = Depends(get_db), user: User = Depends(current_user)):
    """CSVИмпортлох(): бүтэц шалгах → мөр шалгах → давхардал алгасах → нэг гүйлгээгээр хадгалах.

    Алдаатай мөрийг (мөрийн дугаар, шалтгаан) буцаана (Бүлэг 2, Зураг: өгөгдөл импортлох).
    """
    _version_for_edit(db, user, version_id)
    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise HTTPException(400, "Файл UTF-8 кодчилолтой байх ёстой") from e
    required = ["code", "text"] if kind == "clo" else ["type", "title"]
    try:
        res = parse_csv(content, required)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    errors = [ImportRowError(row=r, reason=m) for r, m in res.errors]
    d = load_dictionary(db)
    imported = 0
    if kind == "clo":
        existing = set(db.scalars(select(Clo.code).where(Clo.version_id == version_id)))
        for n, row in _numbered(res):
            if row["code"] in existing:
                errors.append(ImportRowError(row=n, reason=f"{row['code']} код бүртгэлтэй байна"))
                continue
            if len(row["code"]) > 10:
                errors.append(ImportRowError(row=n, reason="Код 10 тэмдэгтээс урт"))
                continue
            c = Clo(version_id=version_id, code=row["code"], text=row["text"])
            _auto_level(c, c.text, d)
            db.add(c)
            existing.add(row["code"])
            imported += 1
    else:
        for n, row in _numbered(res):
            t = row["type"].lower()
            if t not in ITEM_TYPES:
                errors.append(ImportRowError(row=n, reason=f"Төрөл буруу: «{row['type']}» "
                                                           f"({', '.join(ITEM_TYPES)})"))
                continue
            if len(row["title"]) > 200:
                errors.append(ImportRowError(row=n, reason="Гарчиг 200 тэмдэгтээс урт"))
                continue
            i = LearningItem(version_id=version_id, type=t, title=row["title"], text=row.get("text") or "",
                             question_text=row.get("question_text") or None)
            _auto_level(i, item_text(i), d)
            db.add(i)
            imported += 1
    db.commit()
    return ImportOut(imported=imported, errors=sorted(errors, key=lambda e: e.row))


def _numbered(res):
    """parse_csv-ийн хүчинтэй мөрүүдэд анхны файлын мөрийн дугаарыг сэргээнэ."""
    bad = {r for r, _ in res.errors}
    n = 1
    for row in res.rows:
        n += 1
        while n in bad:
            n += 1
        yield n, row


def _not_found(what: str):
    raise HTTPException(404, f"{what} олдсонгүй")
