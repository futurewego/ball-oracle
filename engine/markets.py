from engine.scoreline import poisson_pmf


def outcome_1x2(matrix: list[list[float]]) -> dict:
    """胜平负：主胜/平/客胜（全场 90 分钟口径）。"""
    home = draw = away = 0.0
    for i, row in enumerate(matrix):
        for j, p in enumerate(row):
            if i > j:
                home += p
            elif i == j:
                draw += p
            else:
                away += p
    return {"home": home, "draw": draw, "away": away}


def handicap_1x2(matrix: list[list[float]], handicap: int) -> dict:
    """让球胜平负。handicap = 加到主队净胜球上的整数（主队让1球→-1，客队让2球→+2）。"""
    home = draw = away = 0.0
    for i, row in enumerate(matrix):
        for j, p in enumerate(row):
            adj = (i + handicap) - j
            if adj > 0:
                home += p
            elif adj == 0:
                draw += p
            else:
                away += p
    return {"home": home, "draw": draw, "away": away}


_HOME_SCORES = [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2),
                (4, 0), (4, 1), (4, 2), (5, 0), (5, 1), (5, 2)]
_DRAW_SCORES = [(0, 0), (1, 1), (2, 2), (3, 3)]
_AWAY_SCORES = [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3),
                (0, 4), (1, 4), (2, 4), (0, 5), (1, 5), (2, 5)]


def correct_score(matrix: list[list[float]]) -> dict:
    """比分 31 项：12 主胜具体 + 胜其它 / 4 平具体 + 平其它 / 12 客胜具体 + 负其它。"""
    n = len(matrix)

    def cell(i, j):
        return matrix[i][j] if i < n and j < n else 0.0

    result = {}
    for (i, j) in _HOME_SCORES:
        result[f"{i}:{j}"] = cell(i, j)
    for (i, j) in _DRAW_SCORES:
        result[f"{i}:{j}"] = cell(i, j)
    for (i, j) in _AWAY_SCORES:
        result[f"{i}:{j}"] = cell(i, j)

    o = outcome_1x2(matrix)
    result["胜其它"] = o["home"] - sum(cell(i, j) for i, j in _HOME_SCORES)
    result["平其它"] = o["draw"] - sum(cell(i, j) for i, j in _DRAW_SCORES)
    result["负其它"] = o["away"] - sum(cell(i, j) for i, j in _AWAY_SCORES)
    return result


def total_goals(matrix: list[list[float]]) -> dict:
    """总进球数 8 档：0..6 与 7+。"""
    buckets = {str(k): 0.0 for k in range(7)}
    buckets["7+"] = 0.0
    for i, row in enumerate(matrix):
        for j, p in enumerate(row):
            t = i + j
            if t >= 7:
                buckets["7+"] += p
            else:
                buckets[str(t)] += p
    return buckets


def _sign(home: int, away: int) -> str:
    if home > away:
        return "胜"
    if home == away:
        return "平"
    return "负"


def half_full(lam_home: float, lam_away: float, c: float = 0.45,
              max_goals: int = 8) -> dict:
    """半全场 9 项。上半场 λ*c、下半场 λ*(1-c) 两段独立泊松，相加得全场，
    由 (上半场结果, 全场结果) 联合分布导出。保留 HT 与 FT 相关性。"""
    lh1, la1 = lam_home * c, lam_away * c
    lh2, la2 = lam_home * (1 - c), lam_away * (1 - c)

    keys = ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"]
    result = {k: 0.0 for k in keys}

    rng = range(max_goals + 1)
    for h1 in rng:
        for a1 in rng:
            p_ht = poisson_pmf(h1, lh1) * poisson_pmf(a1, la1)
            if p_ht == 0.0:
                continue
            ht = _sign(h1, a1)
            for h2 in rng:
                for a2 in rng:
                    p_2h = poisson_pmf(h2, lh2) * poisson_pmf(a2, la2)
                    ft = _sign(h1 + h2, a1 + a2)
                    result[ht + ft] += p_ht * p_2h
    total = sum(result.values())
    return {k: v / total for k, v in result.items()}
