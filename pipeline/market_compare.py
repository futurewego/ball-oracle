"""真实竞彩 SP vs 模型概率 对比（须能直连 sporttery 的网络）。

诊断用：暴露模型与市场的系统性分歧。**不产出投注建议**（validated=False）。
"""
import json
from pipeline.odds import SportterySource
from pipeline.value import evaluate_market


def main():
    sp_matches = SportterySource().fetch()
    pred = {(m["home_cn"], m["away_cn"]): m
            for m in json.load(open("build/predictions.json", encoding="utf-8"))["matches"]}
    print(f"竞彩在售 {len(sp_matches)} 场；与模型匹配如下（SP为实时，价值标记恒关）：\n")
    fav_gap = []
    for sm in sp_matches:
        key = (sm["home_cn"], sm["away_cn"])
        if key not in pred or not sm["had"]:
            continue
        r = evaluate_market(pred[key]["spf"], sm["had"], validated=False)
        lab = {"home": sm["home_cn"], "draw": "平", "away": sm["away_cn"]}
        print(f"{sm['home_cn']} vs {sm['away_cn']}")
        for k, v in r.items():
            print(f"  {lab[k]:8} 模型{v['model_p']*100:4.0f}%  市场{v['market_p']*100:4.0f}%"
                  f"  EV{v['ev']*100:+6.1f}%")
        # 记录热门(市场最高项)的 模型−市场 差
        fav = max(r.values(), key=lambda v: v["market_p"])
        fav_gap.append(fav["model_p"] - fav["market_p"])
    if fav_gap:
        avg = sum(fav_gap) / len(fav_gap)
        print(f"\n诊断：模型对'市场热门'的平均概率差 = {avg*100:+.1f}个百分点"
              f"（负值=模型系统性低估热门）")


if __name__ == "__main__":
    main()
