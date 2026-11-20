"""UC4 Холбоос баталгаажуулах (ФШ-19, 20, 24). Control: Холбоос, ӨөрчлөлтийнТүүх.

Эндээс эхэлж хэрэгжүүлнэ. Загварыг programs.py-аас харна уу."""
from fastapi import APIRouter

from app.api.deps import todo

router = APIRouter(prefix="/api", tags=["links"])


@router.get("/links/{link_id}")
def get_link(link_id: int):
    """үндэслэлАвах(): хоёр талын текст, оноо, таарсан үг, түвшин — А10"""
    todo("А10")

@router.post("/links")
def create_manual_link():
    """гараарҮүсгэх() — А10"""
    todo("А10")

@router.post("/links/{link_id}/confirm")
def confirm_link(link_id: int):
    """батлах() — А10"""
    todo("А10")

@router.post("/links/{link_id}/strength")
def change_strength(link_id: int):
    """хүчӨөрчлөх() — А10"""
    todo("А10")

@router.post("/links/{link_id}/reject")
def reject_link(link_id: int):
    """татгалзах() — А10"""
    todo("А10")

@router.get("/links/{link_id}/history")
def link_history(link_id: int):
    """холбоосынТүүхАвах() — А10"""
    todo("А10")
