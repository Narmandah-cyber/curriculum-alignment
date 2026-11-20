"""UC6 Хөтөлбөр, PLO бүртгэх (ФШ-03). Control: Хөтөлбөр, PLO. Хариуцагч: А4.

ЖИШИГ ХЭРЭГЖИЛТ: list/create/plo нэмэх-ийг бүрэн хийсэн. Бусад router-ийг энэ загвараар бичнэ.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_role, todo
from app.db.session import get_db
from app.models import Plo, Program, User
from app.schemas import PloIn, PloOut, ProgramIn, ProgramOut

router = APIRouter(prefix="/api", tags=["programs"])


@router.get("/programs", response_model=list[ProgramOut])
def list_programs(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(Program).order_by(Program.name)).all()


@router.post("/programs", response_model=ProgramOut, status_code=201)
def create_program(body: ProgramIn, db: Session = Depends(get_db),
                   user: User = Depends(require_role("coordinator", "admin"))):
    p = Program(name=body.name, major_code=body.major_code, coordinator_id=user.id)
    db.add(p)
    db.commit()
    return p


@router.get("/programs/{program_id}/plos", response_model=list[PloOut])
def list_plos(program_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(Plo).where(Plo.program_id == program_id).order_by(Plo.code)).all()


@router.post("/programs/{program_id}/plos", response_model=PloOut, status_code=201)
def add_plo(program_id: int, body: PloIn, db: Session = Depends(get_db),
            _: User = Depends(require_role("coordinator"))):
    if not db.get(Program, program_id):
        raise HTTPException(404, "Хөтөлбөр олдсонгүй")
    plo = Plo(program_id=program_id, code=body.code, text=body.text)
    db.add(plo)
    db.commit()
    return plo


@router.patch("/programs/{program_id}")
def update_program(program_id: int):
    todo("А4")


@router.delete("/programs/{program_id}")
def delete_program(program_id: int):
    todo("А4")


@router.patch("/plos/{plo_id}")
def update_plo(plo_id: int):
    todo("А4")


@router.delete("/plos/{plo_id}")
def delete_plo(plo_id: int):
    todo("А4")


@router.post("/programs/{program_id}/courses/{course_id}")
def attach_course(program_id: int, course_id: int):
    todo("А4")


@router.delete("/programs/{program_id}/courses/{course_id}")
def detach_course(program_id: int, course_id: int):
    todo("А4")
