import math
from ratings.metrics import brier_score, log_loss, reliability_table

CLASSES = ("home", "draw", "away")


def test_brier_perfect_is_zero():
    probs = [{"home": 1.0, "draw": 0.0, "away": 0.0}]
    assert brier_score(probs, ["home"]) == 0.0


def test_brier_known_value():
    # 均匀预测、真值 home：sum((1/3-1)^2 + (1/3)^2 + (1/3)^2) = 2/3
    probs = [{"home": 1 / 3, "draw": 1 / 3, "away": 1 / 3}]
    assert math.isclose(brier_score(probs, ["home"]), 2 / 3, rel_tol=1e-9)


def test_log_loss_perfect_near_zero():
    probs = [{"home": 0.999999, "draw": 0.0000005, "away": 0.0000005}]
    assert log_loss(probs, ["home"]) < 1e-5


def test_reliability_table_bins_counts():
    probs = [{"home": 0.9, "draw": 0.05, "away": 0.05},
             {"home": 0.1, "draw": 0.8, "away": 0.1}]
    table = reliability_table(probs, ["home", "draw"], n_bins=10)
    total = sum(row["count"] for row in table)
    assert total == 6  # 2 场 × 3 类
