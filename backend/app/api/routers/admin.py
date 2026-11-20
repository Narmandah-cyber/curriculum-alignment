"""UC11 Жишиг өгөгдөл, тохиргоо удирдах (ФШ-09, 11). Control: ШинжилгээнийТохиргоо, БлумынТоль, CS2023Нэгж.

Эндээс эхэлж хэрэгжүүлнэ. Загварыг programs.py-аас харна уу."""
from fastapi import APIRouter

from app.api.deps import todo

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/settings")
def list_settings():
    """list_settings — А3"""
    todo("А3")

@router.put("/settings/{key}")
def set_setting(key: str):
    """утгаШалгах() → утгаОноох() — А3"""
    todo("А3")

@router.get("/bloom-verbs")
def list_bloom_verbs():
    """list_bloom_verbs — А3"""
    todo("А3")

@router.post("/bloom-verbs")
def add_bloom_verb():
    """add_bloom_verb — А3"""
    todo("А3")

@router.delete("/bloom-verbs/{verb_id}")
def delete_bloom_verb(verb_id: int):
    """delete_bloom_verb — А3"""
    todo("А3")

@router.post("/cs2023/import")
def import_cs2023():
    """жишигАчаалах(файл) — А5"""
    todo("А5")

@router.get("/cs2023")
def search_cs2023():
    """?area=&q= — А5"""
    todo("А5")
