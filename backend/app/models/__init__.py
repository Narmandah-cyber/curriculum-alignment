"""ӨС-ийн загварууд (ERD, Бүлэг 3, Зураг: Өгөгдлийн ерөнхий схем).

ENTITY классууд: хүснэгт бүрт нэг класс. Нэрийн харгалзааг docs/LOOKUP.md-ээс харна.
Энэ файлыг өөрчилсний дараа: `alembic revision --autogenerate -m "..."`.
"""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """Хэрэглэгч (users)."""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # давтагдашгүй дугаар
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)  # овог нэр
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)  # нэвтрэх имэйл
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # bcrypt хэш
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # идэвхтэй эсэх
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())  # үүсгэсэн огноо

class Role(Base):
    """Үүрэг (roles)."""
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)  # teacher / coordinator / admin

class UserRole(Base):
    """Хэрэглэгчийн үүрэг (user_roles)."""
    __tablename__ = "user_roles"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)  # → users
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)  # → roles

class Program(Base):
    """Хөтөлбөр (programs)."""
    __tablename__ = "programs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # хөтөлбөрийн нэр
    major_code: Mapped[str] = mapped_column(String(20), nullable=False)  # мэргэжлийн индекс
    coordinator_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)  # → users

class Plo(Base):
    """PLO (plos)."""
    __tablename__ = "plos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False)  # → programs
    code: Mapped[str] = mapped_column(String(10), nullable=False)  # PLO1 ...
    text: Mapped[str] = mapped_column(Text, nullable=False)  # үр дүнгийн текст
    bloom_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # 1–6

class Course(Base):
    """Хичээл (courses)."""
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # хичээлийн код
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    credits: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # кредит
    teacher_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)  # → users

class ProgramCourse(Base):
    """Хөтөлбөрийн хичээл (program_courses)."""
    __tablename__ = "program_courses"
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), primary_key=True)  # → programs
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)  # → courses

class CourseVersion(Base):
    """Хичээлийн хувилбар (course_versions)."""
    __tablename__ = "course_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)  # → courses
    version_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # хувилбарын дугаар
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)  # 2026–2027
    status: Mapped[str] = mapped_column(String(10), nullable=False)  # active / history
    previous_version_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("course_versions.id"), nullable=True)  # → course_versions
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

class Clo(Base):
    """CLO (clos)."""
    __tablename__ = "clos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("course_versions.id", ondelete="CASCADE"), nullable=False)  # → course_versions
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    bloom_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # 1–6
    level_source: Mapped[str | None] = mapped_column(String(6), nullable=True)  # auto / manual

class LearningItem(Base):
    """Сургалтын элемент (learning_items)."""
    __tablename__ = "learning_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("course_versions.id", ondelete="CASCADE"), nullable=False)  # → course_versions
    type: Mapped[str] = mapped_column(String(12), nullable=False)  # lecture / lab / assignment / exam
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # шалгалтын асуулт
    bloom_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    level_source: Mapped[str | None] = mapped_column(String(6), nullable=True)

class Cs2023Unit(Base):
    """CS2023 нэгж (cs2023_units)."""
    __tablename__ = "cs2023_units"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    area_code: Mapped[str] = mapped_column(String(5), nullable=False)  # SE, DM, ...
    unit_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class PostingBatch(Base):
    """Зарлалын багц (posting_batches)."""
    __tablename__ = "posting_batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("programs.id"), nullable=False)  # → programs
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

class JobPosting(Base):
    """Ажлын зарлал (job_postings)."""
    __tablename__ = "job_postings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("posting_batches.id", ondelete="CASCADE"), nullable=False)  # → posting_batches
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # хувийн мэдээлэлгүй текст
    posted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)  # эх сурвалж
    skills_found: Mapped[bool] = mapped_column(Boolean, nullable=False)  # ур чадвар илэрсэн эсэх

class Skill(Base):
    """Ур чадвар (skills)."""
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_form: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)  # хэвийн хэлбэр
    synonyms: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ижил утгатай хэлбэрүүд

class PostingSkill(Base):
    """Зарлалын ур чадвар (posting_skills)."""
    __tablename__ = "posting_skills"
    posting_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), primary_key=True)  # → job_postings
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)  # → skills

class AnalysisRun(Base):
    """Шинжилгээ (analysis_runs)."""
    __tablename__ = "analysis_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scope: Mapped[str] = mapped_column(String(8), nullable=False)  # course / program
    version_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("course_versions.id"), nullable=True)  # → course_versions (NULL)
    program_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("programs.id"), nullable=True)  # → programs (NULL)
    batch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("posting_batches.id"), nullable=True)  # → posting_batches (NULL)
    method: Mapped[str] = mapped_column(String(10), nullable=False)  # rule / embedding / hybrid
    threshold: Mapped[float] = mapped_column(Float, nullable=False)  # θ
    status: Mapped[str] = mapped_column(String(10), nullable=False)  # running / done / failed
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)  # 0–100
    started_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)  # → users
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Link(Base):
    """Холбоос (links)."""
    __tablename__ = "links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("analysis_runs.id"), nullable=True)  # → analysis_runs (NULL)
    source_type: Mapped[str] = mapped_column(String(10), nullable=False)  # clo / plo
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_type: Mapped[str] = mapped_column(String(10), nullable=False)  # item / plo / cs2023 / skill
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    strength: Mapped[str] = mapped_column(String(8), nullable=False)  # direct / partial
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 0–1
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    level_gap: Mapped[str] = mapped_column(String(8), nullable=False)  # match / below / above
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="proposed")  # proposed / confirmed / rejected
    llm_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

class LinkHistory(Base):
    """Өөрчлөлтийн түүх (link_history)."""
    __tablename__ = "link_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link_id: Mapped[int] = mapped_column(Integer, ForeignKey("links.id", ondelete="CASCADE"), nullable=False)  # → links
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)  # → users
    field: Mapped[str] = mapped_column(String(20), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

class Report(Base):
    """Тайлан (reports)."""
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("analysis_runs.id"), nullable=True)  # → analysis_runs
    format: Mapped[str] = mapped_column(String(4), nullable=False)  # pdf / csv
    file_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

class BloomVerb(Base):
    """Блумын үйл үг (bloom_verbs)."""
    __tablename__ = "bloom_verbs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    verb: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1–6

class Setting(Base):
    """Тохиргоо (settings)."""
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(40), primary_key=True)  # model, threshold, lambda, ...
    value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
