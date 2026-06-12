"""端到端价值演示：模型概率 + (样例)SP → 去水位 + EV。

⚠️ 此处 SP 为**手填样例**，非真实竞彩数据；仅证明价值管线能跑通。
真实 SP 接入后(国内侧)、且历史回测验证模型能赢市场后(§9.7)，
才把 validated 置真、对外展示价值标记。
"""
import json
from pipeline.value import evaluate_market

# 从已生成预测里取一场
pred = json.load(open("build/predictions.json", encoding="utf-8"))
m = next(x for x in pred["matches"] if x["home_cn"] == "巴西")

# 样例 SP（手填，演示用）——主胜/平/客胜
SAMPLE_SPF_SP = {"home": 2.10, "draw": 3.30, "away": 3.40}


def main():
    print(f"演示比赛: {m['home_cn']} vs {m['away_cn']}（⚠️ SP 为手填样例，非真实）")
    print(f"模型胜平负: {m['spf']}")
    print(f"样例 SP:    {SAMPLE_SPF_SP}\n")
    r = evaluate_market(m["spf"], SAMPLE_SPF_SP, method="shin", validated=False)
    print(f"{'选项':6}{'模型概率':>10}{'市场概率':>10}{'SP':>7}{'EV':>9}{'价值?':>8}")
    label = {"home": m["home_cn"], "draw": "平", "away": m["away_cn"]}
    for k, v in r.items():
        print(f"{label[k]:6}{v['model_p']*100:>9.1f}%{v['market_p']*100:>9.1f}%"
              f"{v['sp']:>7}{v['ev']:>+9.2%}{str(v['is_value']):>8}")
    print("\n注：价值列恒为 False —— 诚实闸门(未经回测验证不标记价值)。")


if __name__ == "__main__":
    main()
