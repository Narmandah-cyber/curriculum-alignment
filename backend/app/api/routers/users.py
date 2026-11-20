"""UC10 Хэрэглэгч, эрх удирдах (ФШ-02). Control: Хэрэглэгч.

Эндээс эхэлж хэрэгжүүлнэ. Загварыг programs.py-аас харна уу."""
from fastapi import APIRouter

from app.api.deps import todo

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users")
def list_users():
    """Бүх хэрэглэгч (админ) — А3"""
    todo("А3")

@router.post("/users")
def create_user():
    """Хэрэглэгч үүсгэх, үүрэг оноох — А3"""
    todo("А3")

@router.patch("/users/{user_id}")
def update_user(user_id: int):
    """мэдээлэлЗасах(), идэвхгүйБолгох() — А3"""
    todo("А3")

@router.post("/users/{user_id}/roles/{role}")
def grant_role(user_id: int, role: str):
    """үүрэгОноох() — А3"""
    todo("А3")

@router.delete("/users/{user_id}/roles/{role}")
def revoke_role(user_id: int, role: str):
    """үүрэгЦуцлах() — А3"""
    todo("А3")
