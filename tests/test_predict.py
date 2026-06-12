import math
from engine import predict


def test_predict_returns_all_five_markets():
    r = predict(1.5, 1.2)
    assert set(r.keys()) == {"spf", "handicap", "correct_score", "total_goals", "half_full"}


def test_predict_all_markets_sum_to_one():
    r = predict(1.5, 1.2)
    assert math.isclose(sum(r["spf"].values()), 1.0, rel_tol=1e-9)
    assert math.isclose(sum(r["handicap"].values()), 1.0, rel_tol=1e-9)
    assert math.isclose(sum(r["correct_score"].values()), 1.0, rel_tol=1e-9)
    assert math.isclose(sum(r["total_goals"].values()), 1.0, rel_tol=1e-9)
    assert math.isclose(sum(r["half_full"].values()), 1.0, rel_tol=1e-9)


def test_predict_handicap_uses_given_line():
    r = predict(1.8, 1.0, handicap=-1)
    base = predict(1.8, 1.0, handicap=0)
    assert r["handicap"]["home"] < base["handicap"]["home"]


def test_predict_rejects_nonpositive_lambda():
    import pytest
    with pytest.raises(ValueError):
        predict(0.0, 1.2)
