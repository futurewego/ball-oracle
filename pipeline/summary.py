"""规则模板生成"人话"解读（自包含、可验证）。

留好接口：以后把 match_summary 换成 Claude API 调用即可升级为更自然的锐评，
其余流程不变。
"""


def _confidence_label(p: float) -> str:
    if p >= 0.55:
        return "信心较高"
    if p >= 0.42:
        return "略有倾向"
    return "胶着难分"


def match_summary(home_cn: str, away_cn: str, probs: dict) -> str:
    """由 5 玩法概率生成一句中文解读。home_cn/away_cn 为中文队名。"""
    spf = probs["spf"]
    # 主胜/平/客胜里最可能的方向
    direction, p = max(spf.items(), key=lambda kv: kv[1])
    side = {"home": home_cn, "draw": "平局", "away": away_cn}[direction]
    conf = _confidence_label(p)

    # 最可能比分
    top_cs = max(probs["correct_score"].items(), key=lambda kv: kv[1])[0]
    # 最可能总进球档
    top_tg = max(probs["total_goals"].items(), key=lambda kv: kv[1])[0]

    if direction == "draw":
        lead = f"模型看{home_cn}与{away_cn}{conf}、平局概率最高({p:.0%})"
    else:
        lead = f"模型{conf}倾向{side}({p:.0%})"
    return f"{lead}；最可能比分 {top_cs}，总进球约 {top_tg} 球。"
