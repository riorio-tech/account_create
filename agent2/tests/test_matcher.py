import pytest

from matcher import get_best_match, get_top_matches


def test_get_best_match_biyou_top_tier():
    r = get_best_match("美容")
    assert r["best_creator_type"] in ("エンタメ系", "ライフスタイル系")
    assert r["cvr_expectation"] == "最高"


def test_get_best_match_gadget_senmon():
    r = get_best_match("ガジェット")
    assert r["best_creator_type"] == "専門系"
    assert r["cvr_expectation"] == "高"


def test_unknown_category_raises():
    with pytest.raises(ValueError, match="matrix.jsonに存在しません"):
        get_best_match("存在しないカテゴリ")


def test_get_top_matches_biyou_n2():
    r = get_top_matches("美容", 2)
    assert len(r) == 2


def test_get_top_matches_shokuhin_n1():
    r = get_top_matches("食品", 1)
    assert len(r) == 1
