"""WC2026 物理条件对 λ 的调整层（§9.4）。

⚠️ 重要：本层系数是**保守先验，未经回测验证**。卡塔尔2022/德国2024 不含墨西哥
高原与美国酷暑，无法用现有回测集校准这些效应。因此：
- 所有调整默认 **no-op**（不给条件就不动 λ）；
- 系数刻意取小、单调方向有据（高原/高温→降低体能与进球；少休息→降低）；
- 上线后应随真实 2026 赛果**在线校准**，不可声称已验证。

用法：在评分给出基线 (λ_home, λ_away) 后，按该场场馆/气候/赛程施加。
东道主（美/加/墨）主场优势不在此处——用预测时 neutral=False 走已有 home_adv。
"""


def _altitude_factor(elevation_m: float, team_home_alt_m: float,
                     k: float = 0.06, cap_m: float = 2500.0) -> float:
    """海拔体能折扣：球队主场海拔远低于赛地时耐力受损。

    deficit = max(0, 赛地海拔 − 球队主场海拔)，封顶 cap_m。
    海平面球队在墨西哥城(2240m)约得 0.95 折扣（k=0.06）。
    """
    deficit = max(0.0, elevation_m - team_home_alt_m)
    return 1.0 - k * min(deficit, cap_m) / cap_m


def _heat_factor(temp_c: float, k: float = 0.05,
                 threshold_c: float = 25.0, cap_c: float = 15.0) -> float:
    """高温降速折扣：超过阈值后节奏变慢、进球略降，作用于双方。

    40°C 约得 0.95 折扣（k=0.05, 阈值25, 封顶+15）。
    """
    excess = max(0.0, temp_c - threshold_c)
    return 1.0 - k * min(excess, cap_c) / cap_c


def _rest_factor(rest_days: float, k: float = 0.04,
                 ideal_days: float = 4.0) -> float:
    """休息不足折扣：少于理想休息天数则略降（旅行疲劳的近似）。"""
    deficit = max(0.0, ideal_days - rest_days)
    return 1.0 - k * deficit / ideal_days


def apply_conditions(lam_home: float, lam_away: float, *,
                     elevation_m: float = 0.0,
                     temp_c: float | None = None,
                     home_altitude_m: float = 0.0,
                     away_altitude_m: float = 0.0,
                     home_rest_days: float | None = None,
                     away_rest_days: float | None = None) -> tuple[float, float]:
    """对基线 λ 施加 WC2026 物理调整。不给条件的项不生效（no-op）。"""
    fh = fa = 1.0

    # 海拔：各队按自身主场海拔与赛地的差施加
    if elevation_m > 0.0:
        fh *= _altitude_factor(elevation_m, home_altitude_m)
        fa *= _altitude_factor(elevation_m, away_altitude_m)

    # 高温：作用于双方
    if temp_c is not None:
        f = _heat_factor(temp_c)
        fh *= f
        fa *= f

    # 休息/旅行：各队独立
    if home_rest_days is not None:
        fh *= _rest_factor(home_rest_days)
    if away_rest_days is not None:
        fa *= _rest_factor(away_rest_days)

    return lam_home * fh, lam_away * fa
