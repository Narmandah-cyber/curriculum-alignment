"""Б4: Блумын толь + ангилагч (ФШ-11, ФШ-12)."""
from app.services.bloom.classifier import BloomClassifier
from app.services.bloom.levels import BloomDictionary, assess, level_name, load_seed_verbs

D = BloomDictionary(load_seed_verbs())


def test_seed_verbs_loaded():
    assert len(D.verbs) >= 30 and D.verbs["зохиох"] == 6


def test_conjugated_verbs_and_highest_level():
    r = D.detect("ER диаграм зохиож, хэвийн хэлбэрийг тайлбарлана")
    assert r.level == 6 and r.matched_verb == "зохиох" and r.source == "verb"
    assert D.detect("SQL JOIN ашигласан хүсэлт").level == 3
    assert D.detect("Хүснэгтийг харьцуулж шинжлэх").level == 4


def test_deverbal_nouns_not_matched():
    # «үнэлгээ», «шинжилгээ» нь нэр үг — 5-р түвшин гэж андуурахгүй
    assert D.detect("Явцын үнэлгээ") is None


def test_multiword_phrase():
    assert BloomDictionary({"жишээ гаргах": 2}).detect("Бодит жишээ гаргаж өгөх").level == 2


def test_classifier_fallback_with_reason():
    r = assess("Primary key гэж юу вэ?", D)
    assert r.source == "classifier" and r.level == 1 and r.reason.startswith("Ангилагч")
    assert 0 < r.confidence <= 1


def test_classifier_deterministic():
    c = BloomClassifier()
    assert c.classify("Design a database schema") == c.classify("Design a database schema")
    assert c.classify("Design a database schema").level == 6


def test_level_name():
    assert level_name(4) == "задлан шинжлэх" and level_name(None) == ""
