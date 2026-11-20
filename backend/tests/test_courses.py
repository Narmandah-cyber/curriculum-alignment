"""Б2, Б3: хичээл, CLO, сургалтын элемент, CSV импорт, хувилбар (UC2, UC12; ФШ-04..07, 21; ФБШ-04)."""
import pytest

from tests.conftest import make_user, token


@pytest.fixture()
def teacher(client, db):
    make_user(db, "t@example.com", ["teacher"])
    return token(client, "t@example.com")


def new_course(client, h, code="ӨС201", year="2026-2027"):
    r = client.post("/api/courses", json={"code": code, "name": "Өгөгдлийн сан", "credits": 3,
                                          "academic_year": year}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_course_makes_active_version(client, teacher):
    c = new_course(client, teacher)
    assert c["active_version"]["version_no"] == 1 and c["active_version"]["status"] == "active"
    assert c["summary"]["analyzed"] is False
    assert [x["code"] for x in client.get("/api/courses", headers=teacher).json()] == ["ӨС201"]


def test_duplicate_course_code(client, teacher):
    new_course(client, teacher)
    r = client.post("/api/courses", json={"code": "ӨС201", "name": "x", "credits": 3}, headers=teacher)
    assert r.status_code == 409


def test_only_teacher_role_creates_course(client, db):
    make_user(db, "a@example.com", ["admin"])
    h = token(client, "a@example.com")
    assert client.post("/api/courses", json={"code": "X1", "name": "x", "credits": 3}, headers=h).status_code == 403


def test_clo_crud_and_auto_bloom(client, teacher):
    vid = new_course(client, teacher)["active_version"]["id"]
    r = client.post(f"/api/versions/{vid}/clos", json={"code": "CLO1", "text": "ER диаграм зохиох"}, headers=teacher)
    assert r.status_code == 201
    clo = r.json()
    assert clo["bloom_level"] == 6 and clo["level_source"] == "auto" and "зохиох" in clo["level_reason"]
    # Код давхардал
    assert client.post(f"/api/versions/{vid}/clos", json={"code": "CLO1", "text": "x"},
                       headers=teacher).status_code == 409
    # ФШ-21: гараар засах
    r = client.patch(f"/api/clos/{clo['id']}", json={"bloom_level": 4}, headers=teacher).json()
    assert r["bloom_level"] == 4 and r["level_source"] == "manual" and r["level_reason"] == "Гараар зассан"
    # Текст засахад гараар зассан түвшин хэвээр
    r = client.patch(f"/api/clos/{clo['id']}", json={"text": "Ойлголтыг тайлбарлах"}, headers=teacher).json()
    assert r["bloom_level"] == 4
    # Автомат руу буцаах
    r = client.patch(f"/api/clos/{clo['id']}", json={"bloom_level": None}, headers=teacher).json()
    assert r["bloom_level"] == 2 and r["level_source"] == "auto"
    assert client.delete(f"/api/clos/{clo['id']}", headers=teacher).status_code == 204
    assert client.get(f"/api/versions/{vid}/clos", headers=teacher).json() == []


def test_item_crud(client, teacher):
    vid = new_course(client, teacher)["active_version"]["id"]
    r = client.post(f"/api/versions/{vid}/items", json={"type": "exam", "title": "Ирц шалгалт",
                                                        "question_text": "Primary key гэж юу вэ?"}, headers=teacher)
    assert r.status_code == 201
    item = r.json()
    assert item["bloom_level"] == 1 and item["level_reason"].startswith("Ангилагч")
    assert client.post(f"/api/versions/{vid}/items", json={"type": "quiz", "title": "x"},
                       headers=teacher).status_code == 422
    r = client.patch(f"/api/items/{item['id']}", json={"title": "Явцын шалгалт", "question_text": None},
                     headers=teacher).json()
    assert r["title"] == "Явцын шалгалт" and r["question_text"] is None
    assert client.delete(f"/api/items/{item['id']}", headers=teacher).status_code == 204


def test_other_teacher_forbidden(client, db, teacher):
    vid = new_course(client, teacher)["active_version"]["id"]
    make_user(db, "t2@example.com", ["teacher"])
    h2 = token(client, "t2@example.com")
    assert client.post(f"/api/versions/{vid}/clos", json={"code": "CLO1", "text": "x"}, headers=h2).status_code == 403
    assert client.get(f"/api/versions/{vid}/clos", headers=h2).status_code == 403
    make_user(db, "c@example.com", ["coordinator"])
    hc = token(client, "c@example.com")
    assert client.get(f"/api/versions/{vid}/clos", headers=hc).status_code == 200      # харж болно
    assert len(client.get("/api/courses?mine=false", headers=hc).json()) == 1


def test_csv_import_reports_row_errors(client, teacher):
    vid = new_course(client, teacher)["active_version"]["id"]
    csv = "code,text\nCLO1,Ойлголтыг тайлбарлах\nCLO2,\nCLO1,Ойлголтыг тайлбарлах\nCLO3,SQL хүсэлт бичиж ашиглах\n"
    r = client.post(f"/api/versions/{vid}/import?kind=clo", files={"file": ("c.csv", csv.encode(), "text/csv")},
                    headers=teacher)
    assert r.status_code == 200, r.text
    assert r.json()["imported"] == 2 and [e["row"] for e in r.json()["errors"]] == [3, 4]
    # Дахин импортлоход код давхардана → мөрийн дугаартай алдаа
    r = client.post(f"/api/versions/{vid}/import?kind=clo",
                    files={"file": ("c.csv", b"code,text\nCLO9,a\nCLO3,b\n", "text/csv")}, headers=teacher)
    assert r.json()["imported"] == 1 and r.json()["errors"][0]["row"] == 3

    items = "type,title,text,question_text\nlecture,Лекц 1,ER загвар,\nquiz,Тест,x,\nexam,Шалгалт,,3NF хүртэл хэвийн болго\n"
    r = client.post(f"/api/versions/{vid}/import?kind=item",
                    files={"file": ("i.csv", items.encode(), "text/csv")}, headers=teacher).json()
    assert r["imported"] == 2 and r["errors"][0]["row"] == 3 and "Төрөл" in r["errors"][0]["reason"]


def test_csv_import_wrong_columns(client, teacher):
    vid = new_course(client, teacher)["active_version"]["id"]
    r = client.post(f"/api/versions/{vid}/import?kind=clo", files={"file": ("c.csv", b"name\nx\n", "text/csv")},
                    headers=teacher)
    assert r.status_code == 400 and "Дутуу багана" in r.json()["detail"]


def test_renew_version_history_and_compare(client, teacher, db):
    c = new_course(client, teacher, year="2025-2026")
    v1 = c["active_version"]["id"]
    client.post(f"/api/versions/{v1}/clos", json={"code": "CLO1", "text": "ER диаграм зохиох"}, headers=teacher)
    client.post(f"/api/versions/{v1}/clos", json={"code": "CLO2", "text": "XML өгөгдөл"}, headers=teacher)
    client.post(f"/api/versions/{v1}/items", json={"type": "lab", "title": "Лаб 7", "text": "XML"}, headers=teacher)

    r = client.post(f"/api/courses/{c['id']}/versions", json={"academic_year": "2026-2027"}, headers=teacher)
    assert r.status_code == 201
    v2 = r.json()
    assert v2["version_no"] == 2 and v2["clo_count"] == 2 and v2["previous_version_id"] == v1
    # Ижил онтой хувилбар давхардахгүй
    assert client.post(f"/api/courses/{c['id']}/versions", json={"academic_year": "2026-2027"},
                       headers=teacher).status_code == 409
    versions = client.get(f"/api/courses/{c['id']}/versions", headers=teacher).json()
    assert [(x["version_no"], x["status"]) for x in versions] == [(2, "active"), (1, "history")]
    # Түүх хувилбарыг засахгүй (409)
    assert client.post(f"/api/versions/{v1}/clos", json={"code": "CLO9", "text": "x"},
                       headers=teacher).status_code == 409

    clos2 = {x["code"]: x for x in client.get(f"/api/versions/{v2['id']}/clos", headers=teacher).json()}
    client.patch(f"/api/clos/{clos2['CLO1']['id']}", json={"text": "ER диаграм зохиож 3NF хүртэл хэвийн болгох"},
                 headers=teacher)
    client.delete(f"/api/clos/{clos2['CLO2']['id']}", headers=teacher)
    client.post(f"/api/versions/{v2['id']}/clos", json={"code": "CLO11", "text": "NoSQL загваруудыг харьцуулах"},
                headers=teacher)
    cmp = client.get(f"/api/versions/compare?v1={v1}&v2={v2['id']}", headers=teacher).json()
    assert (cmp["added"], cmp["modified"], cmp["removed"]) == (1, 1, 1)
    assert [(x["change"], x["key"]) for x in cmp["changes"]] == [("added", "CLO11"), ("modified", "CLO1"),
                                                               ("removed", "CLO2")]


def test_renew_copies_confirmed_links(client, teacher, db):
    from app.models import Link
    c = new_course(client, teacher)
    v1 = c["active_version"]["id"]
    clo = client.post(f"/api/versions/{v1}/clos", json={"code": "CLO1", "text": "SQL"}, headers=teacher).json()
    it = client.post(f"/api/versions/{v1}/items", json={"type": "lab", "title": "SQL"}, headers=teacher).json()
    db.add(Link(source_type="clo", source_id=clo["id"], target_type="item", target_id=it["id"], strength="direct",
                score=0.9, method="rule", level_gap="match", status="confirmed"))
    db.add(Link(source_type="clo", source_id=clo["id"], target_type="item", target_id=it["id"], strength="partial",
                score=0.6, method="rule", level_gap="match", status="proposed"))
    db.commit()
    v2 = client.post(f"/api/courses/{c['id']}/versions", json={"academic_year": "2027-2028"}, headers=teacher).json()
    new_clo = client.get(f"/api/versions/{v2['id']}/clos", headers=teacher).json()[0]
    copied = db.query(Link).filter(Link.source_id == new_clo["id"]).all()
    assert len(copied) == 1 and copied[0].status == "confirmed"


def test_delete_course(client, teacher):
    c = new_course(client, teacher)
    client.post(f"/api/courses/{c['id']}/versions", json={"academic_year": "2027-2028"}, headers=teacher)
    assert client.delete(f"/api/courses/{c['id']}", headers=teacher).status_code == 204
    assert client.get(f"/api/courses/{c['id']}", headers=teacher).status_code == 404
