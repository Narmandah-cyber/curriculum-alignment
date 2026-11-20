import pytest

from app.services.bloom.levels import level_from_verbs, level_gap
from app.services.importers.csv_import import parse_csv, remove_pii
from app.services.nlp.preprocess import normalize
from app.services.nlp.similarity import cosine, hybrid_score, keyword_score


def test_normalize():
    assert normalize("  Өгөгдлийн   САН! ") == "өгөгдлийн сан"


def test_cosine_example_from_thesis():
    # Бүлэг 1/хурлын слайдын жишээ: u=(1,2,0), v=(2,1,1) → 4/√30 ≈ 0.73
    assert cosine([1, 2, 0], [2, 1, 1]) == pytest.approx(0.730, abs=1e-3)


def test_hybrid_and_keyword():
    assert hybrid_score(0.74, 0.40, 0.7) == pytest.approx(0.638)
    assert keyword_score("өгөгдлийн сан", "өгөгдлийн сангийн загвар") > 0


def test_bloom():
    verbs = {"тайлбарлах": 2, "зохиох": 6}
    assert level_from_verbs("ER диаграм зохиож тайлбарлана", verbs) == 6
    assert level_from_verbs("юу ч биш", verbs) is None
    assert level_gap(1, 6) == "below" and level_gap(3, 3) == "match" and level_gap(5, 2) == "above"


def test_csv_import_errors_and_duplicates():
    res = parse_csv("code,text\nCLO1,a\nCLO2,\nCLO1,a\n", ["code", "text"])
    assert len(res.rows) == 1 and [e[0] for e in res.errors] == [3, 4]
    with pytest.raises(ValueError):
        parse_csv("code\nCLO1\n", ["code", "text"])


def test_remove_pii():
    assert remove_pii("Холбоо барих: 9911-2233, a.b@mail.mn") == "Холбоо барих: [утас], [имэйл]"
