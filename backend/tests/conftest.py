"""Тестүүд SQLite санах ойн ӨС дээр ажиллана (PostgreSQL шаардлагагүй)."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Role, User, UserRole

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def db():
    Base.metadata.create_all(engine)
    s = TestingSession()
    yield s
    s.close()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(db, email: str, roles: list[str], password: str = "pass1234") -> User:
    u = User(full_name=email.split("@")[0], email=email, password_hash=hash_password(password))
    db.add(u)
    db.flush()
    for name in roles:
        r = db.query(Role).filter_by(name=name).first() or Role(name=name)
        db.add(r)
        db.flush()
        db.add(UserRole(user_id=u.id, role_id=r.id))
    db.commit()
    return u


def token(client, email: str, password: str = "pass1234") -> dict:
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
