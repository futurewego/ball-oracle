from engine.scoreline import score_matrix
from engine.markets import (
    outcome_1x2,
    handicap_1x2,
    correct_score,
    total_goals,
    half_full,
)


def predict(lam_home: float, lam_away: float, rho: float = -0.05,
            handicap: int = 0) -> dict:
    """由两队期望进球导出竞彩 5 大玩法概率。

    lam_home/lam_away: 期望进球，必须 >0。
    rho: Dixon-Coles 低分修正（默认 -0.05）。
    handicap: 让球线（主队净胜球加整数，主-1→-1）。
    """
    if lam_home <= 0 or lam_away <= 0:
        raise ValueError("lam_home 与 lam_away 必须为正")
    m = score_matrix(lam_home, lam_away, rho=rho)
    return {
        "spf": outcome_1x2(m),
        "handicap": handicap_1x2(m, handicap),
        "correct_score": correct_score(m),
        "total_goals": total_goals(m),
        "half_full": half_full(lam_home, lam_away),
    }
