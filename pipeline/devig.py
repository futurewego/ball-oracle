"""去水位：竞彩 SP 赔率 → 市场隐含概率（方案 §4.1）。

竞彩 SP 含水位(Σ 1/SP > 1)。两法：
- multiplicative: 简单归一 p_i = (1/SP_i) / Σ(1/SP)
- shin: Shin(1992) 法，对大冷门去水更准，估计内幕交易比例 z
返还率 RTP = 1 / Σ(1/SP)（实测竞彩主流盘约 0.86）。
"""
from scipy.optimize import brentq


def booksum(sps):
    return sum(1.0 / s for s in sps)


def rtp(sps):
    """返还率 = 1 / 水位和。<1 表示存在水位。"""
    return 1.0 / booksum(sps)


def multiplicative(sps):
    """简单归一去水位，返回与 sps 同序的概率列表。"""
    inv = [1.0 / s for s in sps]
    tot = sum(inv)
    return [x / tot for x in inv]


def _shin_probs(sps, z):
    bs = booksum(sps)
    out = []
    for s in sps:
        bi = 1.0 / s
        val = (z * z + 4.0 * (1.0 - z) * bi * bi / bs) ** 0.5
        out.append((val - z) / (2.0 * (1.0 - z)))
    return out


def shin(sps):
    """Shin 去水位。求解 z 使 Σπ=1；失败则退回 multiplicative。"""
    if len(sps) < 2:
        return multiplicative(sps)
    f = lambda z: sum(_shin_probs(sps, z)) - 1.0
    try:
        if f(1e-9) <= 0:           # 无水位/极小，直接归一
            return multiplicative(sps)
        z = brentq(f, 1e-9, 0.999)
        p = _shin_probs(sps, z)
        tot = sum(p)
        return [x / tot for x in p]  # 数值保险再归一
    except (ValueError, ZeroDivisionError):
        return multiplicative(sps)
