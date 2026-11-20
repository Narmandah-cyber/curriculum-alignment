"""UC9 Тайлан татах (ФШ-25). Control: Тайлан.

Эндээс эхэлж хэрэгжүүлнэ. Загварыг programs.py-аас харна уу."""
from fastapi import APIRouter

from app.api.deps import todo

router = APIRouter(prefix="/api", tags=["reports"])


@router.post("/runs/{run_id}/reports")
def create_report(run_id: int):
    """?format=pdf|csv — А12"""
    todo("А12")

@router.get("/reports/{report_id}/download")
def download_report(report_id: int):
    """download_report — А12"""
    todo("А12")
