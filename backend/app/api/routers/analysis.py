"""UC3, UC8 уялдааг үнэлэх (ФШ-10..18, ФБШ-02). Control: ХичээлийнШинжилгээ, ХөтөлбөрийнШинжилгээ.

Эндээс эхэлж хэрэгжүүлнэ. Загварыг programs.py-аас харна уу."""
from fastapi import APIRouter

from app.api.deps import todo

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/courses/{course_id}/analysis")
def run_course_analysis(course_id: int):
    """body: {method, llm} → AnalysisRun (арын ажил) — Б5"""
    todo("Б5")

@router.post("/programs/{program_id}/analysis")
def run_program_analysis(program_id: int):
    """body: {batch_id, min_frequency} — А9"""
    todo("А9")

@router.get("/runs/{run_id}")
def get_run(run_id: int):
    """Төлөв, явц (%) — А11"""
    todo("А11")

@router.get("/versions/{version_id}/matrix")
def course_matrix(version_id: int):
    """CLO × элемент (ФШ-22) — Б5"""
    todo("Б5")

@router.get("/versions/{version_id}/gaps")
def course_gaps(version_id: int):
    """Хамрагдаагүй CLO, зорилгогүй элемент, түвшний зөрүү (ФШ-12, 13) — Б5"""
    todo("Б5")

@router.get("/programs/{program_id}/matrix")
def program_matrix(program_id: int):
    """?kind=plo-course|plo-cs2023 (ФШ-23) — А9"""
    todo("А9")

@router.get("/runs/{run_id}/missing-skills")
def missing_skills(run_id: int):
    """Хөтөлбөрт дутуу ур чадвар (ФШ-18) — А9"""
    todo("А9")
