"""API-ийн оролт, гаралтын схемүүд (Pydantic). Шинэ модуль нэмэхдээ энд схемээ нэмнэ."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORM):
    id: int
    full_name: str
    email: str
    is_active: bool
    roles: list[str] = []


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    roles: list[str] = ["teacher"]


class ProgramIn(BaseModel):
    name: str
    major_code: str


class ProgramOut(ORM):
    id: int
    name: str
    major_code: str
    coordinator_id: int | None


class PloIn(BaseModel):
    code: str
    text: str


class PloOut(ORM):
    id: int
    program_id: int
    code: str
    text: str
    bloom_level: int | None


class RunOut(ORM):
    id: int
    scope: str
    method: str
    status: str
    progress: int
    started_at: datetime | None
