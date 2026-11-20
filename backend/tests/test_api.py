from tests.conftest import make_user, token


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_and_me(client, db):
    make_user(db, "teacher@example.com", ["teacher"])
    h = token(client, "teacher@example.com")
    me = client.get("/api/auth/me", headers=h).json()
    assert me["email"] == "teacher@example.com" and me["roles"] == ["teacher"]


def test_wrong_password(client, db):
    make_user(db, "t@example.com", ["teacher"])
    assert client.post("/api/auth/login", data={"username": "t@example.com", "password": "x"}).status_code == 401


def test_program_and_plo(client, db):
    make_user(db, "c@example.com", ["coordinator"])
    h = token(client, "c@example.com")
    p = client.post("/api/programs", json={"name": "Програм хангамж", "major_code": "D061301"}, headers=h)
    assert p.status_code == 201
    pid = p.json()["id"]
    assert client.post(f"/api/programs/{pid}/plos", json={"code": "PLO1", "text": "..."}, headers=h).status_code == 201
    assert len(client.get(f"/api/programs/{pid}/plos", headers=h).json()) == 1


def test_teacher_cannot_create_program(client, db):
    make_user(db, "t2@example.com", ["teacher"])
    h = token(client, "t2@example.com")
    assert client.post("/api/programs", json={"name": "x", "major_code": "y"}, headers=h).status_code == 403


def test_stub_returns_501(client):
    assert client.get("/api/users").status_code == 501
