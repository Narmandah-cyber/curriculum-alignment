"""UC: нэвтрэх (ФШ-01). Control: Хэрэглэгч.нэвтрэх(), нууцҮгШалгах(). Хариуцагч: А2."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, user_roles
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas import Token, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Имэйл эсвэл нууц үг буруу")
    return Token(access_token=create_access_token(user.id, user_roles(db, user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    out = UserOut.model_validate(user)
    out.roles = user_roles(db, user.id)
    return out
