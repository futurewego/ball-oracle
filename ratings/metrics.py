import math

CLASSES = ("home", "draw", "away")


def brier_score(probs: list[dict], outcomes: list[str]) -> float:
    """多分类 Brier：每场 Σ_k (p_k − y_k)^2 的均值（越低越好）。"""
    total = 0.0
    for p, y in zip(probs, outcomes):
        total += sum((p[k] - (1.0 if k == y else 0.0)) ** 2 for k in CLASSES)
    return total / len(probs)


def log_loss(probs: list[dict], outcomes: list[str], eps: float = 1e-15) -> float:
    """对数损失：−mean(log p_真值)（越低越好）。"""
    total = 0.0
    for p, y in zip(probs, outcomes):
        total += -math.log(min(max(p[y], eps), 1.0))
    return total / len(probs)


def reliability_table(probs: list[dict], outcomes: list[str],
                      n_bins: int = 10) -> list[dict]:
    """把所有 (类预测概率, 是否命中) 摊平后按概率分箱，比较预测均值 vs 经验频率。"""
    bins = [{"pred_sum": 0.0, "hit": 0, "count": 0} for _ in range(n_bins)]
    for p, y in zip(probs, outcomes):
        for k in CLASSES:
            pk = p[k]
            idx = min(int(pk * n_bins), n_bins - 1)
            bins[idx]["pred_sum"] += pk
            bins[idx]["hit"] += 1 if k == y else 0
            bins[idx]["count"] += 1
    table = []
    for i, b in enumerate(bins):
        c = b["count"]
        table.append({
            "bin": i,
            "pred_mean": b["pred_sum"] / c if c else 0.0,
            "emp_freq": b["hit"] / c if c else 0.0,
            "count": c,
        })
    return table
