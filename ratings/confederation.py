"""洲际强度校正（§9.4/§0.1）——修正跨洲过度评分。

问题：评分在洲内校准，弱洲球队(如 AFC)靠暴打同洲弱旅刷高 attack/defense，
跨洲对阵被系统性高估。世界杯全是跨洲对阵，此偏差必须修。

修法：给每个洲一个 offset δ_c，对该洲所有队的 attack 与 defense **同时减 δ_c**。
- 洲内对阵：两队 attack/defense 各减同量 → λ 不变（见 engine 的平移不变性）。
- 跨洲对阵：才产生净调整，把过度评分的洲拉回。
δ_c 由历史跨洲比赛"实际进失球 vs 原始评分预测"的偏差估计。
"""
import datetime
import math

from ratings.model import Ratings
from ratings.lam import expected_goals

# WC2026 参赛队 + 主要球队 → 洲际。未列入者不校正（δ=0）。
CONFEDERATION = {
    # UEFA
    "Netherlands": "UEFA", "Spain": "UEFA", "Germany": "UEFA", "Switzerland": "UEFA",
    "England": "UEFA", "France": "UEFA", "Portugal": "UEFA", "Croatia": "UEFA",
    "Belgium": "UEFA", "Italy": "UEFA", "Bosnia and Herzegovina": "UEFA",
    "Norway": "UEFA", "Austria": "UEFA", "Scotland": "UEFA", "Denmark": "UEFA",
    "Poland": "UEFA", "Serbia": "UEFA", "Ukraine": "UEFA", "Turkey": "UEFA",
    "Czech Republic": "UEFA", "Sweden": "UEFA", "England": "UEFA",
    # CONMEBOL
    "Brazil": "CONMEBOL", "Argentina": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Colombia": "CONMEBOL", "Paraguay": "CONMEBOL", "Ecuador": "CONMEBOL",
    "Chile": "CONMEBOL", "Peru": "CONMEBOL", "Bolivia": "CONMEBOL", "Venezuela": "CONMEBOL",
    # AFC
    "Japan": "AFC", "South Korea": "AFC", "Iran": "AFC", "Australia": "AFC",
    "Saudi Arabia": "AFC", "Qatar": "AFC", "Iraq": "AFC", "Uzbekistan": "AFC",
    "Jordan": "AFC", "United Arab Emirates": "AFC",
    # CAF
    "Morocco": "CAF", "Senegal": "CAF", "Nigeria": "CAF", "Egypt": "CAF",
    "Tunisia": "CAF", "Algeria": "CAF", "Ghana": "CAF", "Cameroon": "CAF",
    "South Africa": "CAF", "Ivory Coast": "CAF", "Cape Verde": "CAF", "Mali": "CAF",
    "DR Congo": "CAF",
    # CONCACAF
    "Mexico": "CONCACAF", "United States": "CONCACAF", "Canada": "CONCACAF",
    "Costa Rica": "CONCACAF", "Panama": "CONCACAF", "Jamaica": "CONCACAF",
    "Honduras": "CONCACAF", "Curaçao": "CONCACAF", "Haiti": "CONCACAF",
    # OFC
    "New Zealand": "OFC",
}


def confederation_offsets(history, ratings: Ratings,
                          since: datetime.date = datetime.date(2014, 1, 1)) -> dict:
    """由跨洲历史比赛估计每洲 δ_c（正=过度评分，需下调）。"""
    # 累计每洲：实际进球、模型预测进球（仅跨洲、双方都已映射的比赛）
    scored = {}      # conf -> 实际进球
    pred = {}        # conf -> 预测进球(λ)
    for m in history:
        if m.date < since:
            continue
        ch, ca = CONFEDERATION.get(m.home), CONFEDERATION.get(m.away)
        if ch is None or ca is None or ch == ca:
            continue
        lam_h, lam_a = expected_goals(ratings, m.home, m.away, neutral=m.neutral)
        for conf, actual, predicted in [(ch, m.home_score, lam_h),
                                        (ca, m.away_score, lam_a)]:
            scored[conf] = scored.get(conf, 0.0) + actual
            pred[conf] = pred.get(conf, 0.0) + predicted

    # 进攻比值 ratio<1 → 实际比预测少 → 过度评分 → δ>0
    offsets = {}
    for conf in scored:
        if pred[conf] > 0 and scored[conf] > 0:
            ratio = scored[conf] / pred[conf]
            offsets[conf] = -math.log(ratio)
        else:
            offsets[conf] = 0.0
    # 中心化：让平均 δ=0，仅保留洲间相对差
    if offsets:
        mean = sum(offsets.values()) / len(offsets)
        offsets = {c: v - mean for c, v in offsets.items()}
    return offsets


def apply_offsets(ratings: Ratings, offsets: dict) -> Ratings:
    """对各队 attack 与 defense 同时减去其洲 δ_c，返回新 Ratings。"""
    def adj(team, base):
        conf = CONFEDERATION.get(team)
        return base - offsets.get(conf, 0.0) if conf else base

    return Ratings(
        attack={t: adj(t, v) for t, v in ratings.attack.items()},
        defense={t: adj(t, v) for t, v in ratings.defense.items()},
        home_adv=ratings.home_adv,
        rho=ratings.rho,
    )
