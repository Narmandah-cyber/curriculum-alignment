"""API-ийн оролт, гаралтын схемүүд (Pydantic). Шинэ модуль нэмэхдээ энд схемээ нэмнэ."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


# ---------------------------------------------------------------------------
# Хичээл, хувилбар, CLO, сургалтын элемент (UC2, UC12; Б2, Б3)
# ---------------------------------------------------------------------------
ItemType = Literal["lecture", "lab", "assignment", "exam"]
Strength = Literal["direct", "partial"]
Method = Literal["rule", "embedding", "hybrid"]


class CourseIn(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    credits: int = Field(ge=1, le=10)
    academic_year: str = Field(default="2026-2027", pattern=r"^\d{4}[-–]\d{4}$")


class CourseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    credits: int | None = Field(default=None, ge=1, le=10)


class VersionOut(ORM):
    id: int
    course_id: int
    version_no: int
    academic_year: str
    status: str
    previous_version_id: int | None
    created_at: datetime | None
    clo_count: int = 0
    item_count: int = 0


class CourseSummary(BaseModel):
    """Хянах самбарын үзүүлэлт (proto-02). Хамрах хүрээ = баталгаажсан холбоостой CLO-ийн хувь (ФШ-13)."""
    analyzed: bool = False
    coverage: float = 0.0          # 0–1
    proposed: int = 0              # баталгаажаагүй санал
    uncovered_clos: int = 0
    level_gaps: int = 0            # доогуур + дээгүүр


class CourseOut(ORM):
    id: int
    code: str
    name: str
    credits: int
    teacher_id: int | None
    active_version: VersionOut | None = None
    summary: CourseSummary = CourseSummary()


class RenewIn(BaseModel):
    academic_year: str = Field(pattern=r"^\d{4}[-–]\d{4}$")


class CloIn(BaseModel):
    code: str = Field(min_length=1, max_length=10)
    text: str = Field(min_length=1)
    bloom_level: int | None = Field(default=None, ge=1, le=6)


class CloUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=10)
    text: str | None = Field(default=None, min_length=1)
    bloom_level: int | None = Field(default=None, ge=1, le=6)   # гараар засах (ФШ-21)


class CloOut(ORM):
    id: int
    version_id: int
    code: str
    text: str
    bloom_level: int | None
    level_source: str | None
    level_reason: str | None = None   # үндэслэл (ФШ-11): таарсан үйл үг эсвэл ангилагчийн итгэл


class ItemIn(BaseModel):
    type: ItemType
    title: str = Field(min_length=1, max_length=200)
    text: str = ""
    question_text: str | None = None
    bloom_level: int | None = Field(default=None, ge=1, le=6)


class ItemUpdate(BaseModel):
    type: ItemType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    text: str | None = None
    question_text: str | None = None
    bloom_level: int | None = Field(default=None, ge=1, le=6)


class ItemOut(ORM):
    id: int
    version_id: int
    type: str
    title: str
    text: str
    question_text: str | None
    bloom_level: int | None
    level_source: str | None
    level_reason: str | None = None


class ImportRowError(BaseModel):
    row: int
    reason: str


class ImportOut(BaseModel):
    imported: int
    errors: list[ImportRowError]


class VersionChange(BaseModel):
    change: Literal["added", "modified", "removed"]
    kind: Literal["clo", "item"]
    key: str                      # CLO код эсвэл элементийн гарчиг
    old_text: str | None = None
    new_text: str | None = None


class VersionCompareOut(BaseModel):
    v1: VersionOut
    v2: VersionOut
    added: int
    modified: int
    removed: int
    changes: list[VersionChange]


# ---------------------------------------------------------------------------
# Хичээлийн шинжилгээ, матриц, зөрүү (UC3, UC5; Б5)
# ---------------------------------------------------------------------------
class CourseAnalysisIn(BaseModel):
    method: Method = "hybrid"
    llm: bool = False


class CourseRunOut(RunOut):
    version_id: int | None
    threshold: float
    finished_at: datetime | None
    notice: str | None = None


class MatrixCell(BaseModel):
    link_id: int
    clo_id: int
    item_id: int
    score: float
    strength: str
    status: str
    level_gap: str
    method: str
    matched_terms: list[str] = []
    llm_explanation: str | None = None


class MatrixOut(BaseModel):
    version: VersionOut
    clos: list[CloOut]
    items: list[ItemOut]
    cells: list[MatrixCell]
    run: CourseRunOut | None
    proposed: int
    confirmed: int


class GapLink(BaseModel):
    link_id: int
    clo: CloOut
    item: ItemOut
    level_gap: str
    status: str
    score: float


class UncoveredClo(CloOut):
    has_proposed: bool = False    # санал байгаа ч баталгаажаагүй


class GapsOut(BaseModel):
    match: int
    below: int
    above: int
    unaligned: int
    level_gaps: list[GapLink]
    uncovered_clos: list[UncoveredClo]
    unaligned_items: list[ItemOut]
