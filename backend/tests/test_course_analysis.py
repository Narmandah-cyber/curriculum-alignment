"""Б5: ХичээлийнШинжилгээ, матриц, зөрүү (UC3, UC5; ФШ-10..13, 22, 24; ФБШ-02, 06, 07)."""
import pytest

from app.models import AnalysisRun, Clo, Course, CourseVersion, LearningItem, Link
from app.services.analysis.course import CourseAnalysis, gaps, matched_terms, stems
from tests.conftest import make_user, token


class FakeEmbedder:
    """Үндсийн давтамжийн вектор — embedding загваргүйгээр тест хийхэд."""

    def encode(self, texts):
        vocab = sorted({s for t in texts for s in stems(t)})
        return [[1.0 if v in stems(t) else 0.0 for v in vocab] for t in texts]


@pytest.fixture()
def course(db):
    u = make_user(db, "t@example.com", ["teacher"])
    c = Course(code="ӨС201", name="Өгөгдлийн сан", credits=3, teacher_id=u.id)
    db.add(c)
    db.flush()
    v = CourseVersion(course_id=c.id, version_no=1, academic_year="2026-2027", status="active")
    db.add(v)
    db.flush()
    db.add_all([
        Clo(version_id=v.id, code="CLO1", text="Өгөгдлийн сангийн үндсэн ойлголт, загваруудыг тайлбарлах"),
        Clo(version_id=v.id, code="CLO2", text="Бодит асуудалд ER диаграмм зохиомжлох"),
        Clo(version_id=v.id, code="CLO3", text="SQL хүсэлт бичиж өгөгдөл боловсруулах"),
        LearningItem(version_id=v.id, type="lecture", title="Лекц 3", text="ER загвар, холбоосын төрлүүд"),
        LearningItem(version_id=v.id, type="lab", title="Лаб 2", text="Бодит асуудалд ER диаграмм зохиох"),
        LearningItem(version_id=v.id, type="assignment", title="БД1", text="SQL хүсэлт бичиж ашиглах"),
        LearningItem(version_id=v.id, type="exam", title="Ирц шалгалт", text="",
                     question_text="Primary key гэж юу вэ?"),
    ])
    db.commit()
    return u, c, v


def test_matched_terms():
    assert "sql" in matched_terms("SQL хүсэлт бичих", "БД1. SQL JOIN хүсэлт")


def test_rule_analysis_proposes_links_and_levels(db, course):
    u, _, v = course
    run = CourseAnalysis(db).start(v.id, "rule", u.id)
    assert run.status == "done" and run.progress == 100 and run.method == "rule"
    links = db.query(Link).all()
    assert links and all(lk.status == "proposed" and lk.score >= 0.5 for lk in links)
    clo2 = db.query(Clo).filter_by(code="CLO2").one()
    assert clo2.bloom_level == 6 and clo2.level_source == "auto"
    pairs = {(lk.source_id, lk.target_id) for lk in links}
    lab = db.query(LearningItem).filter_by(title="Лаб 2").one()
    assert (clo2.id, lab.id) in pairs


def test_deterministic(db, course):
    """ФБШ-07: ижил өгөгдөл, тохиргоо → ижил үр дүн."""
    u, _, v = course
    CourseAnalysis(db).start(v.id, "rule", u.id)
    first = sorted((lk.source_id, lk.target_id, lk.score) for lk in db.query(Link).all())
    CourseAnalysis(db).start(v.id, "rule", u.id)
    assert sorted((lk.source_id, lk.target_id, lk.score) for lk in db.query(Link).all()) == first


def test_hybrid_with_embedder(db, course):
    u, _, v = course
    run = CourseAnalysis(db, embedder=FakeEmbedder()).start(v.id, "hybrid", u.id)
    assert run.method == "hybrid" and db.query(Link).filter_by(method="hybrid").count() > 0


def test_embedding_unavailable_falls_back_to_rule(db, course):
    u, _, v = course
    a = CourseAnalysis(db)                      # А6-ийн Embedder.encode → NotImplementedError
    run = a.start(v.id, "embedding", u.id)
    assert run.status == "done" and run.method == "rule" and "дүрэмд" in a.notice


def test_confirmed_links_kept(db, course):
    """UC3 5а: баталгаажсан холбоосыг дахин бичихгүй, зөвхөн шинэ санал нэмнэ."""
    u, _, v = course
    CourseAnalysis(db).start(v.id, "rule", u.id)
    lk = db.query(Link).first()
    lk.status, lk.strength = "confirmed", "partial"
    db.commit()
    CourseAnalysis(db).start(v.id, "rule", u.id)
    same = db.query(Link).filter_by(source_id=lk.source_id, target_id=lk.target_id).all()
    assert len(same) == 1 and same[0].status == "confirmed" and same[0].strength == "partial"


def test_manual_level_not_overwritten(db, course):
    u, _, v = course
    clo = db.query(Clo).filter_by(code="CLO1").one()
    clo.bloom_level, clo.level_source = 5, "manual"
    db.commit()
    CourseAnalysis(db).start(v.id, "rule", u.id)
    assert db.get(Clo, clo.id).bloom_level == 5


def test_gaps(db, course):
    u, _, v = course
    CourseAnalysis(db).start(v.id, "rule", u.id)
    g = gaps(db, v.id)
    # Баталгаажаагүй үед бүх CLO хамрагдаагүй (ФШ-13)
    assert len(g["uncovered"]) == 3
    exam = db.query(LearningItem).filter_by(title="Ирц шалгалт").one()
    assert exam in g["unaligned"]
    lab = db.query(LearningItem).filter_by(title="Лаб 2").one()
    lk = db.query(Link).filter_by(target_id=lab.id).first()
    lk.status = "confirmed"
    db.commit()
    assert len(gaps(db, v.id)["uncovered"]) == 2


def test_failed_run_when_no_items(db, course):
    u, _, v = course
    db.query(LearningItem).delete()
    db.commit()
    assert CourseAnalysis(db).start(v.id, "rule", u.id).status == "failed"


def test_api_analysis_matrix_gaps(client, db, course):
    u, c, v = course
    h = token(client, "t@example.com")
    r = client.post(f"/api/courses/{c.id}/analysis", json={"method": "rule", "llm": True}, headers=h)
    assert r.status_code == 202 and r.json()["status"] == "running" and "LLM" in r.json()["notice"]
    db.expire_all()
    assert db.get(AnalysisRun, r.json()["id"]).status == "done"       # арын ажил дууссан

    m = client.get(f"/api/versions/{v.id}/matrix", headers=h).json()
    assert len(m["clos"]) == 3 and len(m["items"]) == 4 and m["run"]["status"] == "done"
    assert m["cells"] and m["proposed"] == len(m["cells"])
    cell = m["cells"][0]
    assert set(cell) >= {"score", "strength", "level_gap", "matched_terms"}

    g = client.get(f"/api/versions/{v.id}/gaps", headers=h).json()
    assert len(g["uncovered_clos"]) == 3 and g["unaligned"] >= 1
    assert all(x["has_proposed"] in (True, False) for x in g["uncovered_clos"])

    s = client.get(f"/api/courses/{c.id}", headers=h).json()["summary"]
    assert s["analyzed"] and s["proposed"] == m["proposed"] and s["coverage"] == 0.0


def test_api_analysis_requires_owner_and_data(client, db, course):
    _, c, v = course
    make_user(db, "x@example.com", ["teacher"])
    assert client.post(f"/api/courses/{c.id}/analysis", json={"method": "rule"},
                       headers=token(client, "x@example.com")).status_code == 403
    db.query(Clo).delete()
    db.commit()
    assert client.post(f"/api/courses/{c.id}/analysis", json={"method": "rule"},
                       headers=token(client, "t@example.com")).status_code == 409
