"""UC2 Хичээлийн өгөгдөл бүртгэх, UC12 Хичээлийн хөтөлбөр шинэчлэх (ФШ-04..07). Control: Хичээл, ХичээлийнХувилбар, CLO, СургалтынЭлемент.

Эндээс эхэлж хэрэгжүүлнэ. Загварыг programs.py-аас харна уу."""
from fastapi import APIRouter

from app.api.deps import todo

router = APIRouter(prefix="/api", tags=["courses"])


@router.get("/courses")
def list_courses():
    """Багшийн хичээлүүд (хянах самбар) — Б2"""
    todo("Б2")

@router.post("/courses")
def create_course():
    """Хичээл үүсгэх + анхны хувилбар — Б2"""
    todo("Б2")

@router.get("/courses/{course_id}")
def get_course(course_id: int):
    """get_course — Б2"""
    todo("Б2")

@router.patch("/courses/{course_id}")
def update_course(course_id: int):
    """update_course — Б2"""
    todo("Б2")

@router.delete("/courses/{course_id}")
def delete_course(course_id: int):
    """delete_course — Б2"""
    todo("Б2")

@router.get("/courses/{course_id}/versions")
def list_versions(course_id: int):
    """хувилбаруудАвах() — Б3"""
    todo("Б3")

@router.post("/courses/{course_id}/versions")
def renew_course(course_id: int):
    """хөтөлбөрШинэчлэх(хичээлийнЖил): хуулах → түүхэндШилжүүлэх → идэвхжүүлэх — Б3"""
    todo("Б3")

@router.get("/versions/compare")
def compare_versions():
    """?v1=&v2= → ялгааТооцох() — Б3"""
    todo("Б3")

@router.get("/versions/{version_id}/clos")
def list_clos(version_id: int):
    """list_clos — Б2"""
    todo("Б2")

@router.post("/versions/{version_id}/clos")
def add_clo(version_id: int):
    """засахБоломжтойЭсэх() шалгана (түүх бол 409) — Б2"""
    todo("Б2")

@router.patch("/clos/{clo_id}")
def update_clo(clo_id: int):
    """текстЗасах(), блумТүвшинЗасах() (ФШ-21) — Б2"""
    todo("Б2")

@router.delete("/clos/{clo_id}")
def delete_clo(clo_id: int):
    """delete_clo — Б2"""
    todo("Б2")

@router.get("/versions/{version_id}/items")
def list_items(version_id: int):
    """list_items — Б2"""
    todo("Б2")

@router.post("/versions/{version_id}/items")
def add_item(version_id: int):
    """add_item — Б2"""
    todo("Б2")

@router.patch("/items/{item_id}")
def update_item(item_id: int):
    """update_item — Б2"""
    todo("Б2")

@router.delete("/items/{item_id}")
def delete_item(item_id: int):
    """delete_item — Б2"""
    todo("Б2")

@router.post("/versions/{version_id}/import")
def import_csv(version_id: int):
    """CSV импорт (ФШ-06), алдаатай мөрийн жагсаалт буцаана — Б2"""
    todo("Б2")
