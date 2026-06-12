import math
from ratings.model import Ratings
from ratings.backtest import predict_1x2, outcome_of


def _ratings():
    return Ratings(attack={"A": 0.5, "B": -0.5},
                   defense={"A": 0.3, "B": -0.3}, home_adv=0.25, rho=-0.05)


def test_predict_1x2_sums_to_one():
    p = predict_1x2(_ratings(), "A", "B", neutral=True)
    assert math.isclose(p["home"] + p["draw"] + p["away"], 1.0, rel_tol=1e-9)


def test_predict_stronger_home_more_likely():
    p = predict_1x2(_ratings(), "A", "B", neutral=True)
    assert p["home"] > p["away"]


def test_outcome_of():
    assert outcome_of(2, 0) == "home"
    assert outcome_of(1, 1) == "draw"
    assert outcome_of(0, 3) == "away"
