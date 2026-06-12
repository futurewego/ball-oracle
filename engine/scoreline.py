import math


def poisson_pmf(k: int, lam: float) -> float:
    """泊松概率质量 P(X=k; lam)。k<0 返回 0。"""
    if k < 0:
        return 0.0
    return math.exp(-lam) * lam**k / math.factorial(k)


def _dc_tau(i: int, j: int, lam_home: float, lam_away: float, rho: float) -> float:
    """Dixon-Coles 低比分修正因子。"""
    if i == 0 and j == 0:
        return 1.0 - lam_home * lam_away * rho
    if i == 0 and j == 1:
        return 1.0 + lam_home * rho
    if i == 1 and j == 0:
        return 1.0 + lam_away * rho
    if i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(
    lam_home: float,
    lam_away: float,
    rho: float = 0.0,
    max_goals: int = 10,
) -> list[list[float]]:
    """返回归一化的比分联合分布矩阵 m[i][j]=P(主进i, 客进j)。

    rho 为 Dixon-Coles 低分相关参数（典型 -0.1~0）。rho=0 退化为独立泊松。
    """
    raw = [
        [
            _dc_tau(i, j, lam_home, lam_away, rho)
            * poisson_pmf(i, lam_home)
            * poisson_pmf(j, lam_away)
            for j in range(max_goals + 1)
        ]
        for i in range(max_goals + 1)
    ]
    total = sum(cell for row in raw for cell in row)
    return [[cell / total for cell in row] for row in raw]
