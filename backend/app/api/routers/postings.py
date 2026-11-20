"""UC7 Ажлын зарлал оруулах (ФШ-08, ФБШ-05). Control: ЗарлалынБагц, АжлынЗарлал.

Эндээс эхэлж хэрэгжүүлнэ. Загварыг programs.py-аас харна уу."""
from fastapi import APIRouter

from app.api.deps import todo

router = APIRouter(prefix="/api", tags=["postings"])


@router.get("/programs/{program_id}/batches")
def list_batches(program_id: int):
    """list_batches — А7"""
    todo("А7")

@router.post("/programs/{program_id}/batches")
def import_batch(program_id: int):
    """CSV → мөр шалгах → хувийн мэдээлэл арилгах → хадгалах — А7"""
    todo("А7")

@router.get("/batches/{batch_id}/postings")
def list_postings(batch_id: int):
    """Ялгасан ур чадвартай нь — А7"""
    todo("А7")
