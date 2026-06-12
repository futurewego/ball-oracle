import math
from ratings.model import Ratings
from ratings.lam import expected_goals
from ratings.confederation import apply_offsets, CONFEDERATION


def _ratings():
    # Netherlands(UEFA), Spain(UEFA), Japan(AFC)
    return Ratings(
        attack={"Netherlands": 0.9, "Spain": 1.1, "Japan": 1.0},
        defense={"Netherlands": 0.6, "Spain": 0.9, "Japan": 0.95},
        home_adv=0.25, rho=-0.05,
    )


def test_intra_confederation_lambda_unchanged():
    # 洲内对阵(荷兰vs西班牙同属UEFA)：两队同减δ → λ 完全不变（核心不变量）
    r = _ratings()
    offsets = {"UEFA": -0.3, "AFC": 0.1}
    r2 = apply_offsets(r, offsets)
    base = expected_goals(r, "Netherlands", "Spain", neutral=True)
    adj = expected_goals(r2, "Netherlands", "Spain", neutral=True)
    assert math.isclose(base[0], adj[0], rel_tol=1e-9)
    assert math.isclose(base[1], adj[1], rel_tol=1e-9)


def test_cross_confederation_lambda_changes():
    # 跨洲对阵(荷兰UEFA vs 日本AFC)：AFC上调δ后日本被下调
    r = _ratings()
    offsets = {"UEFA": -0.3, "AFC": 0.3}
    r2 = apply_offsets(r, offsets)
    base_jp = expected_goals(r, "Netherlands", "Japan", neutral=True)[1]
    adj_jp = expected_goals(r2, "Netherlands", "Japan", neutral=True)[1]
    assert adj_jp < base_jp  # 日本(AFC,δ>0)进球预期被下调


def test_unmapped_team_not_adjusted():
    r = Ratings(attack={"X": 0.5}, defense={"X": 0.3}, home_adv=0.2, rho=-0.05)
    r2 = apply_offsets(r, {"UEFA": -0.3})
    assert r2.attack["X"] == 0.5 and r2.defense["X"] == 0.3
