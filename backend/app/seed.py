"""Анхны өгөгдөл ачаалах: үүргүүд, админ хэрэглэгч, Блумын толь, CS2023.

Ажиллуулах: python -m app.seed   (ADMIN_EMAIL, ADMIN_PASSWORD орчны хувьсагчийг .env-д тохируулна)
"""
import csv
import os
from pathlib import Path

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import BloomVerb, Cs2023Unit, Role, User, UserRole

SEED = Path(os.getenv("SEED_DIR", Path(__file__).resolve().parents[2] / "data" / "seed"))


def run() -> None:
    db = SessionLocal()
    for name in ("teacher", "coordinator", "admin"):
        if not db.scalar(select(Role).where(Role.name == name)):
            db.add(Role(name=name))
    db.commit()
    email, pw = os.getenv("ADMIN_EMAIL", "admin@example.com"), os.getenv("ADMIN_PASSWORD", "admin123")
    if not db.scalar(select(User).where(User.email == email)):
        u = User(full_name="Админ", email=email, password_hash=hash_password(pw))
        db.add(u)
        db.flush()
        for r in db.scalars(select(Role)):
            db.add(UserRole(user_id=u.id, role_id=r.id))
    if (SEED / "bloom_verbs.csv").exists() and not db.scalar(select(BloomVerb)):
        with open(SEED / "bloom_verbs.csv", encoding="utf-8") as f:
            db.add_all(BloomVerb(verb=r["verb"], level=int(r["level"])) for r in csv.DictReader(f))
    if (SEED / "cs2023_units.csv").exists() and not db.scalar(select(Cs2023Unit)):
        with open(SEED / "cs2023_units.csv", encoding="utf-8") as f:
            db.add_all(Cs2023Unit(**r) for r in csv.DictReader(f))
    db.commit()
    print("seed: ok")


if __name__ == "__main__":
    run()
