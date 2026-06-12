"""闭环编排：赛程 → DC-MLE评分 → 引擎5玩法概率 → 解读 → predictions.json。

零外部凭证。SP/价值层为后续插入点（live SP 须在国内侧抓取，做成 adapter）。
"""
import datetime
import json
import os

from ratings.data import ensure_dataset, load_matches, filter_before
from ratings.model import fit
from ratings.lam import expected_goals
from ratings.confederation import confederation_offsets, apply_offsets
from engine.predict import predict
from pipeline.fixtures import load_fixtures, TOURNAMENT_START
from pipeline.summary import match_summary

OUT_PATH = os.path.join("build", "predictions.json")


def build(out_path: str = OUT_PATH) -> dict:
    fixtures = load_fixtures()

    # 评分：用开赛前的全部国际赛果拟合一次，再做洲际跨洲校正
    history = filter_before(load_matches(ensure_dataset()), TOURNAMENT_START)
    raw_ratings = fit(history, half_life_days=730.0)
    ratings = apply_offsets(raw_ratings, confederation_offsets(history, raw_ratings))

    matches = []
    for fx in fixtures:
        lam_h, lam_a = expected_goals(ratings, fx.home, fx.away, neutral=fx.neutral)
        probs = predict(lam_h, lam_a, rho=ratings.rho)
        home_cn, away_cn = fx.cn.split(" vs ")
        matches.append({
            "date": fx.date.isoformat(),
            "group": fx.group,
            "venue": fx.venue,
            "neutral": fx.neutral,
            "home": fx.home,
            "away": fx.away,
            "home_cn": home_cn,
            "away_cn": away_cn,
            "lam_home": round(lam_h, 2),
            "lam_away": round(lam_a, 2),
            "spf": {k: round(v, 4) for k, v in probs["spf"].items()},
            "total_goals": {k: round(v, 4) for k, v in probs["total_goals"].items()},
            "top_scores": sorted(probs["correct_score"].items(),
                                 key=lambda kv: -kv[1])[:4],
            "summary": match_summary(home_cn, away_cn, probs),
        })

    payload = {
        "generated_for": "2026 FIFA World Cup",
        "model": "Dixon-Coles 双泊松 + 时间/赛事加权 MLE",
        "note": "仅展示模型概率，未含 SP/价值，仅供参考",
        "matches": matches,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


if __name__ == "__main__":
    p = build()
    print(f"生成 {len(p['matches'])} 场预测 -> {OUT_PATH}")
    for m in p["matches"]:
        print(f"  {m['home_cn']} vs {m['away_cn']}: "
              f"主胜{m['spf']['home']:.0%}/平{m['spf']['draw']:.0%}/客胜{m['spf']['away']:.0%}")
