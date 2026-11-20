"""Нийтлэг хамаарал: ӨС-ийн session, нэвтэрсэн хэрэглэгч, үүргээр эрх шалгах (ФБШ-04)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import Role, User, UserRole

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def user_roles(db: Session, user_id: int) -> list[str]:
    q = select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id)
    return list(db.scalars(q))


def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    data = decode_token(token)
    user = db.get(User, int(data["sub"])) if data else None
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Нэвтрэх шаардлагатай")
    return user


def require_role(*roles: str):
    """Жишээ: Depends(require_role("admin"))."""
    def checker(user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
        if not set(roles) & set(user_roles(db, user.id)):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Танд энэ үйлдлийг хийх эрх байхгүй")
        return user
    return checker


def todo(task_id: str):
    """Хэрэгжээгүй endpoint. task_id = docs/ASSIGNMENTS.md дахь ажлын дугаар."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, f"Хэрэгжүүлээгүй байна ({task_id})")
