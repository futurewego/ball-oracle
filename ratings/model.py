import datetime
import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

from ratings.data import Match


@dataclass
class Ratings:
    attack: dict        # team -> float（均值约 0）
    defense: dict       # team -> float
    home_adv: float
    rho: float


def _dc_log_tau(hs, as_, lam_h, lam_a, rho):
    """Dixon-Coles 低分修正的对数（向量化）。仅低分单元 ≠0。"""
    out = np.zeros_like(lam_h)
    m00 = (hs == 0) & (as_ == 0)
    m01 = (hs == 0) & (as_ == 1)
    m10 = (hs == 1) & (as_ == 0)
    m11 = (hs == 1) & (as_ == 1)
    out[m00] = np.log(np.maximum(1 - lam_h[m00] * lam_a[m00] * rho, 1e-12))
    out[m01] = np.log(np.maximum(1 + lam_h[m01] * rho, 1e-12))
    out[m10] = np.log(np.maximum(1 + lam_a[m10] * rho, 1e-12))
    out[m11] = np.log(np.maximum(1 - rho, 1e-12))
    return out


def fit(matches: list[Match], half_life_days: float = 730.0,
        l2: float = 1e-3, max_iter: int = 200) -> Ratings:
    """对一批比赛做时间加权的 Dixon-Coles 极大似然，返回评分。"""
    teams = sorted({m.home for m in matches} | {m.away for m in matches})
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)

    hi = np.array([idx[m.home] for m in matches])
    ai = np.array([idx[m.away] for m in matches])
    hs = np.array([m.home_score for m in matches], dtype=float)
    as_ = np.array([m.away_score for m in matches], dtype=float)
    neutral = np.array([m.neutral for m in matches], dtype=bool)

    t_max = max(m.date for m in matches)
    age = np.array([(t_max - m.date).days for m in matches], dtype=float)
    xi = math.log(2.0) / half_life_days
    w = np.exp(-xi * age)

    lg_hs = gammaln(hs + 1.0)
    lg_as = gammaln(as_ + 1.0)

    def unpack(p):
        attack = p[:n]
        defense = p[n:2 * n]
        home_adv = p[2 * n]
        rho = p[2 * n + 1]
        return attack, defense, home_adv, rho

    def nll(p):
        attack, defense, home_adv, rho = unpack(p)
        log_lh = attack[hi] - defense[ai] + np.where(neutral, 0.0, home_adv)
        log_la = attack[ai] - defense[hi]
        lam_h = np.exp(np.clip(log_lh, -10, 4))
        lam_a = np.exp(np.clip(log_la, -10, 4))
        ll_h = hs * np.log(lam_h) - lam_h - lg_hs
        ll_a = as_ * np.log(lam_a) - lam_a - lg_as
        ll_tau = _dc_log_tau(hs, as_, lam_h, lam_a, rho)
        ll = w * (ll_h + ll_a + ll_tau)
        penalty = l2 * (attack.mean() ** 2 * n + np.sum(attack ** 2)
                        + np.sum(defense ** 2))
        return -(ll.sum()) + penalty

    x0 = np.zeros(2 * n + 2)
    x0[2 * n] = 0.25   # home_adv 初值
    x0[2 * n + 1] = -0.05  # rho 初值
    bounds = [(-3, 3)] * (2 * n) + [(-1, 1), (-0.2, 0.2)]
    res = minimize(nll, x0, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": max_iter})

    attack, defense, home_adv, rho = unpack(res.x)
    attack = attack - attack.mean()  # 强制中心化
    return Ratings(
        attack={t: float(attack[idx[t]]) for t in teams},
        defense={t: float(defense[idx[t]]) for t in teams},
        home_adv=float(home_adv),
        rho=float(rho),
    )
