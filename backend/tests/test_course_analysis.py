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


# --------------------------------------------------------------------------- ФШ-14: CLO–PLO санал
@pytest.fixture()
def with_program(db, course):
    from app.models import Plo, Program, ProgramCourse
    u, c, v = course
    p = Program(name="Програм хангамж", major_code="D061301")
    db.add(p)
    db.flush()
    db.add(ProgramCourse(program_id=p.id, course_id=c.id))
    db.add_all([Plo(program_id=p.id, code="PLO1", text="Бодит асуудалд ER диаграмм зохиомжлох чадвартай", bloom_level=6),
                Plo(program_id=p.id, code="PLO2", text="Багаар ажиллах, харилцааны ур чадвар")])
    db.commit()
    return u, c, v, p


def test_clo_plo_proposals(db, with_program):
    u, _, v, _ = with_program
    CourseAnalysis(db).start(v.id, "rule", u.id)
    lks = db.query(Link).filter_by(target_type="plo").all()
    clo2 = db.query(Clo).filter_by(code="CLO2").one()
    from app.models import Plo
    plo1, plo2 = db.query(Plo).filter_by(code="PLO1").one(), db.query(Plo).filter_by(code="PLO2").one()
    pairs = {(lk.source_id, lk.target_id): lk for lk in lks}
    assert (clo2.id, plo1.id) in pairs and pairs[(clo2.id, plo1.id)].level_gap == "match"
    assert all(lk.target_id != plo2.id for lk in lks)
    assert all(lk.status == "proposed" and lk.score >= 0.5 for lk in lks)
    assert db.get(Plo, plo2.id).bloom_level is None          # PLO-ийн түвшинг өөрчлөхгүй


def test_clo_plo_kept_on_rerun_and_renew(client, db, with_program):
    u, c, v, _ = with_program
    CourseAnalysis(db).start(v.id, "rule", u.id)
    lk = db.query(Link).filter_by(target_type="plo").first()
    lk.status = "confirmed"
    db.commit()
    CourseAnalysis(db).start(v.id, "rule", u.id)
    assert db.query(Link).filter_by(target_type="plo", source_id=lk.source_id, target_id=lk.target_id).count() == 1
    h = token(client, "t@example.com")
    v2 = client.post(f"/api/courses/{c.id}/versions", json={"academic_year": "2027-2028"}, headers=h).json()
    new_ids = [x["id"] for x in client.get(f"/api/versions/{v2['id']}/clos", headers=h).json()]
    copied = db.query(Link).filter(Link.target_type == "plo", Link.source_id.in_(new_ids)).all()
    assert len(copied) == 1 and copied[0].status == "confirmed" and copied[0].target_id == lk.target_id


def test_no_program_no_plo_links(db, course):
    u, _, v = course
    CourseAnalysis(db).start(v.id, "rule", u.id)
    assert db.query(Link).filter_by(target_type="plo").count() == 0


def test_api_clo_plo(client, db, with_program):
    u, c, v, p = with_program
    h = token(client, "t@example.com")
    client.post(f"/api/courses/{c.id}/analysis", json={"method": "rule"}, headers=h)
    r = client.get(f"/api/versions/{v.id}/clo-plo", headers=h).json()
    assert [x["name"] for x in r["programs"]] == [p.name] and len(r["plos"]) == 2 and len(r["clos"]) == 3
    assert r["cells"] and r["proposed"] == len(r["cells"]) and "matched_terms" in r["cells"][0]
    # Матриц (CLO × элемент)-д PLO холбоос орохгүй
    m = client.get(f"/api/versions/{v.id}/matrix", headers=h).json()
    assert {x["item_id"] for x in m["cells"]} <= {i["id"] for i in m["items"]}


def test_history_version_view_readonly(client, db, course):
    """ФШ-07: түүх хувилбарыг харж болно, засахгүй."""
    u, c, v = course
    h = token(client, "t@example.com")
    CourseAnalysis(db).start(v.id, "rule", u.id)
    client.post(f"/api/courses/{c.id}/versions", json={"academic_year": "2027-2028"}, headers=h)
    assert len(client.get(f"/api/versions/{v.id}/clos", headers=h).json()) == 3
    m = client.get(f"/api/versions/{v.id}/matrix", headers=h).json()
    assert m["version"]["status"] == "history" and m["run"]["status"] == "done"
    clo = client.get(f"/api/versions/{v.id}/clos", headers=h).json()[0]
    assert client.patch(f"/api/clos/{clo['id']}", json={"text": "x"}, headers=h).status_code == 409
