import math
from ratings.model import Ratings


def expected_goals(ratings: Ratings, home: str, away: str,
                   neutral: bool = False) -> tuple[float, float]:
    """评分映射为 (λ_home, λ_away)。未知队按均值 0 处理。"""
    a_home = ratings.attack.get(home, 0.0)
    a_away = ratings.attack.get(away, 0.0)
    d_home = ratings.defense.get(home, 0.0)
    d_away = ratings.defense.get(away, 0.0)
    adv = 0.0 if neutral else ratings.home_adv
    lam_h = math.exp(a_home - d_away + adv)
    lam_a = math.exp(a_away - d_home)
    return lam_h, lam_a
