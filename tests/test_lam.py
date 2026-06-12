from ratings.model import Ratings
from ratings.lam import expected_goals


def _ratings():
    return Ratings(
        attack={"A": 0.5, "B": -0.5},
        defense={"A": 0.3, "B": -0.3},
        home_adv=0.25,
        rho=-0.05,
    )


def test_stronger_team_higher_lambda():
    lh, la = expected_goals(_ratings(), "A", "B", neutral=True)
    assert lh > la


def test_home_advantage_applied_when_not_neutral():
    lh_n, _ = expected_goals(_ratings(), "A", "B", neutral=True)
    lh_h, _ = expected_goals(_ratings(), "A", "B", neutral=False)
    assert lh_h > lh_n  # 非中立场主队 λ 更高


def test_unknown_team_uses_average():
    lh, la = expected_goals(_ratings(), "A", "UNKNOWN", neutral=True)
    assert lh > 0 and la > 0  # 未知队按均值(0)处理，不崩
