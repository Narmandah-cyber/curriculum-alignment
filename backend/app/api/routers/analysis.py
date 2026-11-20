"""UC3, UC8 уялдааг үнэлэх (ФШ-10..18, ФБШ-02). Control: ХичээлийнШинжилгээ, ХөтөлбөрийнШинжилгээ.

Хичээлийн тал (UC3, UC5) — Б5; хөтөлбөрийн тал (UC8) — А9; явц (/runs) — А11."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import current_user, todo
from app.api.routers.courses import (
    _course_or_404,
    _version_for_view,
    check_owner,
    clo_out,
    item_out,
    version_out,
)
from app.db.session import get_db
from app.models import AnalysisRun, Clo, LearningItem, Program, ProgramCourse, User
from app.schemas import (
    CloPloCell,
    CloPloOut,
    CourseAnalysisIn,
    CourseRunOut,
    GapLink,
    GapsOut,
    MatrixCell,
    MatrixOut,
    PloOut,
    ProgramOut,
    UncoveredClo,
)
from app.services import versioning
from app.services.analysis.course import (
    CourseAnalysis,
    course_plos,
    gaps,
    item_text,
    matched_terms,
    version_links,
)
from app.services.bloom.levels import load_dictionary

router = APIRouter(prefix="/api", tags=["analysis"])


def _run_in_background(bind, run_id: int, llm: bool) -> None:
    """Арын ажил (ФБШ-02): хүсэлтийн session хаагдсан тул шинэ session нээнэ."""
    db = sessionmaker(bind=bind, expire_on_commit=False)()
    try:
        CourseAnalysis(db).execute(run_id, llm=llm)
    finally:
        db.close()


@router.post("/courses/{course_id}/analysis", response_model=CourseRunOut, status_code=202)
def run_course_analysis(course_id: int, body: CourseAnalysisIn, tasks: BackgroundTasks,
                        db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Хичээл.уялдааҮнэлэх() → ХичээлийнШинжилгээ.эхлүүлэх(идэвхтэй хувилбар, арга) — Б5.

    AnalysisRun(status=running)-г буцааж, шинжилгээг арын ажлаар гүйцэтгэнэ. Явцыг GET /api/runs/{id}.
    """
    c = _course_or_404(db, course_id)
    check_owner(user, c)
    v = versioning.active_version(db, c.id)
    if v is None:
        raise HTTPException(409, "Идэвхтэй хувилбар олдсонгүй")
    has_clo = db.scalar(select(Clo.id).where(Clo.version_id == v.id).limit(1))
    has_item = db.scalar(select(LearningItem.id).where(LearningItem.version_id == v.id).limit(1))
    if not has_clo or not has_item:
        raise HTTPException(409, "Дор хаяж нэг CLO болон нэг сургалтын элемент бүртгэнэ үү (UC3 өмнөх нөхцөл)")
    run = CourseAnalysis(db).create_run(v.id, body.method, user.id)
    tasks.add_task(_run_in_background, db.get_bind(), run.id, body.llm)
    out = CourseRunOut.model_validate(run)
    if body.llm:
        out.notice = "LLM тайлбар (ФШ-26) хараахан холбогдоогүй тул тайлбаргүйгээр үргэлжилнэ."
    return out


@router.post("/programs/{program_id}/analysis")
def run_program_analysis(program_id: int):
    """body: {batch_id, min_frequency} — А9"""
    todo("А9")

@router.get("/runs/{run_id}")
def get_run(run_id: int):
    """Төлөв, явц (%) — А11"""
    todo("А11")

@router.get("/versions/{version_id}/matrix", response_model=MatrixOut)
def course_matrix(version_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Хичээл.матрицҮүсгэх(): CLO × элемент (ФШ-22), нүд бүрийн үндэслэлтэй (ФШ-24) — Б5."""
    v = _version_for_view(db, user, version_id)
    d = load_dictionary(db)
    clos = list(db.scalars(select(Clo).where(Clo.version_id == v.id).order_by(Clo.code)))
    items = list(db.scalars(select(LearningItem).where(LearningItem.version_id == v.id).order_by(LearningItem.id)))
    by_clo, by_item = {c.id: c for c in clos}, {i.id: i for i in items}
    cells = []
    for lk in version_links(db, v.id):
        if lk.status == "rejected" or lk.source_id not in by_clo or lk.target_id not in by_item:
            continue
        c, it = by_clo[lk.source_id], by_item[lk.target_id]
        cells.append(MatrixCell(link_id=lk.id, clo_id=c.id, item_id=it.id, score=lk.score, strength=lk.strength,
                                status=lk.status, level_gap=lk.level_gap, method=lk.method,
                                matched_terms=matched_terms(c.text, item_text(it)),
                                llm_explanation=lk.llm_explanation))
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.version_id == v.id)
                    .order_by(AnalysisRun.id.desc()).limit(1))
    return MatrixOut(version=version_out(db, v), clos=[clo_out(c, d) for c in clos],
                     items=[item_out(i, d) for i in items], cells=cells,
                     run=CourseRunOut.model_validate(run) if run else None,
                     proposed=sum(c.status == "proposed" for c in cells),
                     confirmed=sum(c.status == "confirmed" for c in cells))


@router.get("/versions/{version_id}/clo-plo", response_model=CloPloOut)
def course_clo_plo(version_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """CLO × PLO холбоосын санал (ФШ-14) — Б5. PLO нь хичээл хамааруулсан хөтөлбөрүүдийнх."""
    v = _version_for_view(db, user, version_id)
    d = load_dictionary(db)
    clos = list(db.scalars(select(Clo).where(Clo.version_id == v.id).order_by(Clo.code)))
    plos = course_plos(db, v.id)
    by_clo, by_plo = {c.id: c for c in clos}, {p.id: p for p in plos}
    programs = db.scalars(select(Program).where(Program.id.in_(
        select(ProgramCourse.program_id).where(ProgramCourse.course_id == v.course_id))).order_by(Program.name))
    cells = [CloPloCell(link_id=lk.id, clo_id=lk.source_id, plo_id=lk.target_id, score=lk.score,
                        strength=lk.strength, status=lk.status, level_gap=lk.level_gap, method=lk.method,
                        matched_terms=matched_terms(by_clo[lk.source_id].text, by_plo[lk.target_id].text))
             for lk in version_links(db, v.id, "plo")
             if lk.status != "rejected" and lk.source_id in by_clo and lk.target_id in by_plo]
    return CloPloOut(version=version_out(db, v), programs=[ProgramOut.model_validate(p) for p in programs],
                     plos=[PloOut.model_validate(p) for p in plos], clos=[clo_out(c, d) for c in clos], cells=cells,
                     proposed=sum(c.status == "proposed" for c in cells),
                     confirmed=sum(c.status == "confirmed" for c in cells))


@router.get("/versions/{version_id}/gaps", response_model=GapsOut)
def course_gaps(version_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Хамрагдаагүй CLO, зорилгогүй элемент, түвшний зөрүү (ФШ-12, 13) — Б5."""
    v = _version_for_view(db, user, version_id)
    d = load_dictionary(db)
    g = gaps(db, v.id)
    return GapsOut(
        match=g["match"], below=g["below"], above=g["above"], unaligned=len(g["unaligned"]),
        level_gaps=[GapLink(link_id=lk.id, clo=clo_out(c, d), item=item_out(it, d), level_gap=gap,
                            status=lk.status, score=lk.score) for lk, c, it, gap in g["level_gaps"]],
        uncovered_clos=[UncoveredClo(**clo_out(c, d).model_dump(), has_proposed=p) for c, p in g["uncovered"]],
        unaligned_items=[item_out(i, d) for i in g["unaligned"]],
    )


@router.get("/programs/{program_id}/matrix")
def program_matrix(program_id: int):
    """?kind=plo-course|plo-cs2023 (ФШ-23) — А9"""
    todo("А9")

@router.get("/runs/{run_id}/missing-skills")
def missing_skills(run_id: int):
    """Хөтөлбөрт дутуу ур чадвар (ФШ-18) — А9"""
    todo("А9")
