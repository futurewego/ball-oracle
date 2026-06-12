"""价值判定：模型概率 vs 市场隐含概率 → EV（方案 §4.2）。

诚实闸门：validated=False（默认）时，is_value 永远为 False。
即"未经历史回测验证模型能跑赢市场前，绝不对外标记任何'价值'"。
这把 §9.7 的纪律写进代码，防止无依据推单。
"""
from pipeline.devig import multiplicative, shin


def ev(model_p: float, sp: float) -> float:
    """期望值 EV = 模型概率 × SP − 1。>0 才有正期望。"""
    return model_p * sp - 1.0


def evaluate_market(model_probs: dict, sps: dict, *, method: str = "shin",
                    validated: bool = False, ev_threshold: float = 0.08) -> dict:
    """对一个玩法逐选项算 市场隐含概率/EV/edge/是否价值。

    model_probs、sps 同键(如 home/draw/away)。
    is_value 仅在 validated=True 且 EV>阈值 时为真——否则恒 False（诚实闸门）。
    """
    keys = list(model_probs.keys())
    sp_list = [sps[k] for k in keys]
    market = shin(sp_list) if method == "shin" else multiplicative(sp_list)
    market_p = dict(zip(keys, market))

    out = {}
    for k in keys:
        e = ev(model_probs[k], sps[k])
        out[k] = {
            "model_p": round(model_probs[k], 4),
            "market_p": round(market_p[k], 4),
            "sp": sps[k],
            "ev": round(e, 4),
            "edge": round(model_probs[k] - market_p[k], 4),
            "is_value": bool(validated and e > ev_threshold),
        }
    return out
