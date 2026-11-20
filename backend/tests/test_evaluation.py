"""Туршилтын хэрэгсэл (СА3, СА4): хэмжүүр, загвар гаргах, нэгтгэх, үнэлгээ."""
import pytest

from app.evaluation import metrics as M
from app.evaluation.__main__ import main
from app.evaluation.annotation import (
    AnnotationError,
    export_templates,
    merge,
    read_annotations,
    read_csv,
    split_of,
    write_csv,
)
from app.evaluation.evaluate import agreement, evaluate_bloom, evaluate_gaps, evaluate_links
from app.models import Clo, Course, CourseVersion, LearningItem
from tests.conftest import make_user


# --------------------------------------------------------------------------- хэмжүүр
def test_prf():
    r = M.prf([True, True, False, False], [True, False, True, False])
    assert (r.tp, r.fp, r.fn) == (1, 1, 1) and r.precision == r.recall == r.f1 == 0.5
    assert M.prf([False], [False]).f1 == 0.0


def test_kappa_known_values():
    assert M.cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]) == pytest.approx(0.5)
    assert M.cohen_kappa(list("abc"), list("abc")) == 1.0
    assert M.cohen_kappa(["a", "a"], ["a", "a"]) == 1.0
    assert M.cohen_kappa([1, 0], [0, 1]) == pytest.approx(-1.0)
    assert M.landis_koch(0.7) == "нэлээд" and M.landis_koch(0.85) == "бараг төгс"


def test_macro_f1_and_confusion():
    g, p = ["1", "1", "2", "3"], ["1", "2", "2", "3"]
    assert M.macro_f1(g, p, ["1", "2", "3"]) == pytest.approx((2 / 3 + 2 / 3 + 1) / 3)
    assert M.confusion(g, p, ["1", "2", "3"]) == [[1, 1, 0], [0, 1, 0], [0, 0, 1]]


def test_best_threshold():
    scores, gold = [0.9, 0.8, 0.4, 0.3, 0.6], [True, True, False, False, False]
    best = M.best_threshold(scores, gold, M.grid(0.1, 0.9, 0.1))
    assert best["f1"] == 1.0 and 0.6 < best["threshold"] <= 0.8


def test_split_stable():
    assert split_of("ӨС201|CLO1", 0.3) == split_of("ӨС201|CLO1", 0.3)
    s = [split_of(f"k{i}", 0.3) for i in range(1000)]
    assert 0.25 < s.count("dev") / 1000 < 0.35


# --------------------------------------------------------------------------- загвар гаргах
@pytest.fixture()
def course(db):
    u = make_user(db, "t@example.com", ["teacher"])
    c = Course(code="ӨС201", name="Өгөгдлийн сан", credits=3, teacher_id=u.id)
    db.add(c)
    db.flush()
    v = CourseVersion(course_id=c.id, version_no=1, academic_year="2026-2027", status="active")
    db.add(v)
    db.flush()
    db.add_all([Clo(version_id=v.id, code="CLO1", text="ER диаграмм зохиомжлох", bloom_level=6, level_source="auto"),
                Clo(version_id=v.id, code="CLO2", text="SQL хүсэлт бичиж ашиглах"),
                LearningItem(version_id=v.id, type="lecture", title="Лекц 1", text="ER загвар"),
                LearningItem(version_id=v.id, type="lab", title="Лаб 1", text="ER диаграмм зохиох"),
                LearningItem(version_id=v.id, type="exam", title="Шалгалт", text="", question_text="SQL JOIN бич")])
    db.commit()
    return c


def test_export_templates(db, course, tmp_path):
    r = export_templates(db, ["ӨС201"], tmp_path)
    assert r.links == 6 and r.bloom == 4          # 2 CLO × 3 элемент; 2 CLO + 2 үнэлгээ (лекц орохгүй)
    a, b = read_csv(tmp_path / "links_annotator_A.csv"), read_csv(tmp_path / "links_annotator_B.csv")
    assert {x["pair_id"] for x in a} == {x["pair_id"] for x in b}
    assert all(x["label"] == "" and x["split"] in ("dev", "test") for x in a)
    bl = read_csv(tmp_path / "bloom_annotator_A.csv")
    assert all(x["level"] == "" for x in bl)       # системийн түвшин тэмдэглэгчид харагдахгүй
    assert "Шалгалт SQL JOIN бич" in {x["text"] for x in bl}
    with pytest.raises(AnnotationError):           # тэмдэглэгээг дарж бичихгүй
        export_templates(db, ["ӨС201"], tmp_path)
    with pytest.raises(AnnotationError):
        export_templates(db, ["XX999"], tmp_path / "x")


# --------------------------------------------------------------------------- нэгтгэх, тохироо, үнэлгээ
LINKS = [  # (clo_text, item_type, item_text, A, B, split)
    ("ER диаграмм зохиомжлох", "lab", "Лаб 1 ER диаграмм зохиох", "direct", "direct", "dev"),
    ("ER диаграмм зохиомжлох", "lecture", "Лекц 1 ER загвар диаграмм", "partial", "direct", "dev"),
    ("ER диаграмм зохиомжлох", "exam", "Шалгалт SQL JOIN хүсэлт бич", "none", "none", "dev"),
    ("SQL хүсэлт бичиж ашиглах", "exam", "Шалгалт SQL JOIN хүсэлт бичиж ашиглах", "direct", "direct", "dev"),
    ("SQL хүсэлт бичиж ашиглах", "lab", "Лаб 1 ER диаграмм зохиох", "none", "none", "dev"),
    ("Хэвийн хэлбэрт оруулах", "assignment", "БД2 Хүснэгтийг хэвийн хэлбэрт оруулах", "direct", "partial", "test"),
    ("Хэвийн хэлбэрт оруулах", "lab", "Лаб 1 ER диаграмм зохиох", "none", "none", "test"),
    ("Транзакц тайлбарлах", "exam", "Шалгалт Транзакц ACID тайлбарлах", "direct", "direct", "test"),
    ("Транзакц тайлбарлах", "lecture", "Лекц 5 Индекс", "none", "partial", "test"),
]


def write_links(tmp_path, gold_fill=True):
    rows_a, rows_b = [], []
    for i, (ct, it, txt, la, lb, sp) in enumerate(LINKS):
        base = {"pair_id": f"p{i}", "split": sp, "course": "ӨС201", "clo_id": i, "clo_code": f"CLO{i}", "clo_text": ct,
                "item_id": 100 + i, "item_type": it, "item_title": txt.split()[0], "item_text": txt, "note": ""}
        rows_a.append(base | {"label": la})
        rows_b.append(base | {"label": lb})
    from app.evaluation.annotation import LINK_COLUMNS
    write_csv(tmp_path / "links_annotator_A.csv", LINK_COLUMNS, rows_a)
    write_csv(tmp_path / "links_annotator_B.csv", LINK_COLUMNS, rows_b)


def test_read_annotations_validates(tmp_path):
    from app.evaluation.annotation import LINK_COLUMNS
    write_csv(tmp_path / "x.csv", LINK_COLUMNS, [{"pair_id": "p1", "label": "шууд"}, {"pair_id": "p2", "label": "maybe"},
                                                {"pair_id": "p3", "label": ""}])
    with pytest.raises(AnnotationError) as e:
        read_annotations(tmp_path / "x.csv", "links")
    assert "мөр 3" in str(e.value) and "мөр 4" in str(e.value)
    write_csv(tmp_path / "y.csv", LINK_COLUMNS, [{"pair_id": "p1", "label": "Шууд"}, {"pair_id": "p2", "label": "N"}])
    r = read_annotations(tmp_path / "y.csv", "links")
    assert r["p1"]["label"] == "direct" and r["p2"]["label"] == "none"


def test_agreement_and_merge(tmp_path):
    write_links(tmp_path)
    a = agreement(tmp_path / "links_annotator_A.csv", tmp_path / "links_annotator_B.csv", "links")
    assert a["n"] == 9 and len(a["disagreements"]) == 3 and -1 <= a["kappa"] <= 1 and "kappa_binary" in a
    out = tmp_path / "links_gold.csv"
    r = merge(tmp_path / "links_annotator_A.csv", tmp_path / "links_annotator_B.csv", "links", out)
    assert r["disputed"] == 3
    gold = read_csv(out)
    assert sum(g["disputed"] == "1" and g["label"] == "" for g in gold) == 3
    # Хэлэлцсэний дараа бөглөөд дахин merge хийхэд хадгалагдана
    for g in gold:
        if g["disputed"] == "1":
            g["label"] = g["label_A"]
    write_csv(out, list(gold[0]), gold)
    merge(tmp_path / "links_annotator_A.csv", tmp_path / "links_annotator_B.csv", "links", out)
    assert all(g["label"] for g in read_csv(out))


def test_evaluate_links_rule_and_unavailable_embedding(tmp_path):
    write_links(tmp_path)
    out = tmp_path / "links_gold.csv"
    merge(tmp_path / "links_annotator_A.csv", tmp_path / "links_annotator_B.csv", "links", out)
    gold = read_csv(out)
    for g in gold:
        g["label"] = g["label"] or g["label_A"]
    write_csv(out, list(gold[0]), gold)
    r = evaluate_links(out, methods=("rule", "embedding"))
    rule, emb = r["results"]
    assert rule.available and rule.threshold is not None and 0 <= rule.test.f1 <= 1 and rule.curve
    assert rule.direct_threshold >= rule.threshold
    assert not emb.available and "NotImplementedError" in emb.reason     # А6 хэрэгжээгүй


class FakeEmbedder:
    def encode(self, texts):
        from app.services.analysis.course import stems
        vocab = sorted({s for t in texts for s in stems(t)})
        return [[1.0 if v in stems(t) else 0.0 for v in vocab] for t in texts]


def test_evaluate_links_hybrid_with_embedder(tmp_path):
    write_links(tmp_path)
    out = tmp_path / "links_gold.csv"
    merge(tmp_path / "links_annotator_A.csv", tmp_path / "links_annotator_B.csv", "links", out)
    gold = read_csv(out)
    for g in gold:
        g["label"] = g["label"] or g["label_A"]
    write_csv(out, list(gold[0]), gold)
    r = evaluate_links(out, methods=("hybrid",), embedder=FakeEmbedder())
    assert r["results"][0].available and r["results"][0].test is not None


def test_bloom_and_gaps(tmp_path):
    from app.evaluation.annotation import BLOOM_COLUMNS, LINK_COLUMNS
    bloom = [{"obj_id": "clo:1", "split": "test", "kind": "clo", "code": "CLO1", "text": "ER диаграмм зохиомжлох", "level": "6"},
             {"obj_id": "clo:2", "split": "test", "kind": "clo", "code": "CLO2", "text": "SQL хүсэлт бичиж ашиглах", "level": "3"},
             {"obj_id": "item:10", "split": "test", "kind": "exam", "code": "Ш", "text": "Primary key гэж юу вэ?", "level": "1"},
             {"obj_id": "item:11", "split": "test", "kind": "lab", "code": "Л", "text": "SQL JOIN ашиглан хүсэлт бичих", "level": "3"}]
    write_csv(tmp_path / "bloom_gold.csv", BLOOM_COLUMNS, bloom)
    b = evaluate_bloom(tmp_path / "bloom_gold.csv")
    assert b["n"] == 4 and 0 <= b["macro_f1"] <= 1 and b["by_source"]["classifier"]["n"] >= 1
    links = [{"pair_id": "a", "split": "test", "clo_id": 1, "clo_text": "x", "item_id": 10, "item_type": "exam",
              "item_text": "y", "label": "direct"},
             {"pair_id": "b", "split": "test", "clo_id": 2, "clo_text": "x", "item_id": 11, "item_type": "lab",
              "item_text": "y", "label": "partial"},
             {"pair_id": "c", "split": "test", "clo_id": 1, "clo_text": "x", "item_id": 11, "item_type": "lab",
              "item_text": "y", "label": "none"}]
    write_csv(tmp_path / "links_gold.csv", LINK_COLUMNS, links)
    g = evaluate_gaps(tmp_path / "links_gold.csv", tmp_path / "bloom_gold.csv")
    assert g["n"] == 2 and g["confusion"][0][0] + g["confusion"][1][1] + g["confusion"][2][2] >= 1


def test_cli_end_to_end(tmp_path, capsys):
    write_links(tmp_path)
    assert main(["agreement", "links", "--dir", str(tmp_path)]) == 0
    assert "Cohen's kappa" in capsys.readouterr().out
    assert main(["merge", "links", "--dir", str(tmp_path)]) == 0
    assert main(["evaluate", "--dir", str(tmp_path), "--methods", "rule"]) == 1    # хэлэлцээгүй мөр үлдсэн
    gold = read_csv(tmp_path / "links_gold.csv")
    for g in gold:
        g["label"] = g["label"] or g["label_A"]
    write_csv(tmp_path / "links_gold.csv", list(gold[0]), gold)
    assert main(["evaluate", "--dir", str(tmp_path), "--methods", "rule", "embedding"]) == 0
    res = tmp_path / "results"
    md = (res / "results.md").read_text(encoding="utf-8")
    assert "СА3" in md and "Тэмдэглэгчдийн тохироо" in md and "боломжгүй" in md
    assert (res / "curve_rule.csv").exists() and "tab:sa3-results" in (res / "results.tex").read_text(encoding="utf-8")
