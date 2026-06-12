"""生成"第一轮 AI 分析结论"静态页 web/round1.html。

定位：模型概率分析 / 看球参考，**不是投注建议、不是推单**。
强调：①最可能≠最有价值(未对比赔率,无EV) ②买热门长期亏 ③合规免责。
"""
import json
import os

IN_PATH = os.path.join("build", "predictions.json")
OUT_PATH = os.path.join("web", "round1.html")


def conf_tier(p):
    if p >= 0.55:
        return "高", "信心较高"
    if p >= 0.42:
        return "中", "略有倾向"
    return "低", "胶着难分"


def card(m):
    spf = m["spf"]
    direction, p = max(spf.items(), key=lambda kv: kv[1])
    side = {"home": m["home_cn"], "draw": "平局", "away": m["away_cn"]}[direction]
    tier, _ = conf_tier(p)
    top_cs = m["top_scores"][0][0]
    top_tg = max(m["total_goals"].items(), key=lambda kv: kv[1])[0]
    concl = (f"倾向 <b>{side}</b>（{p*100:.0f}%，信心{tier}）· 最可能比分 {top_cs} · 总进球约 {top_tg} 球"
             if direction != "draw" else
             f"<b>平局</b>概率最高（{p*100:.0f}%）· 最可能比分 {top_cs} · 总进球约 {top_tg} 球")
    pct = lambda x: f"{x*100:.1f}%"
    lbl = lambda x: f"{x*100:.0f}%"
    return f"""
    <article class="card">
      <header><span class="grp">组 {m['group']} · 第1轮</span><span>{m['date']}</span></header>
      <h2>{m['home_cn']} <small>vs</small> {m['away_cn']}</h2>
      <div class="venue">{'东道主主场' if not m['neutral'] else '中立场'} · 预期比分 λ {m['lam_home']} - {m['lam_away']}</div>
      <div class="bar">
        <div class="seg home" style="width:{pct(spf['home'])}"><span>{lbl(spf['home'])}</span></div>
        <div class="seg draw" style="width:{pct(spf['draw'])}"><span>{lbl(spf['draw'])}</span></div>
        <div class="seg away" style="width:{pct(spf['away'])}"><span>{lbl(spf['away'])}</span></div>
      </div>
      <div class="legend"><span><i class="dot home"></i>{m['home_cn']}胜</span><span><i class="dot draw"></i>平</span><span><i class="dot away"></i>{m['away_cn']}胜</span></div>
      <p class="concl">📊 模型结论：{concl}</p>
    </article>"""


CSS = """
:root{--bg:#0b0e14;--card:#141925;--line:#222a3a;--home:#3ea6ff;--draw:#8b93a7;--away:#ff5d73;--txt:#e6e9f0;--mut:#8b93a7}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:"PingFang SC",-apple-system,system-ui,sans-serif;line-height:1.5}
.wrap{max-width:1100px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:23px;letter-spacing:1px}.tag{color:var(--mut);font-size:13px;margin-top:4px}
.warn{margin:16px 0;padding:14px;border:1px solid #4a2a2a;background:#1f1414;border-radius:10px;color:#ffc0c0;font-size:13px;line-height:1.8}
.warn b{color:#ff8f8f}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px;margin-top:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.card header{display:flex;justify-content:space-between;color:var(--mut);font-size:12px}
.grp{background:#1d2740;color:#9fc0ff;padding:1px 8px;border-radius:20px}
.card h2{font-size:19px;margin:8px 0 2px}.card h2 small{color:var(--mut);font-weight:400;font-size:13px}
.venue{color:var(--mut);font-size:12px;margin-bottom:12px}
.bar{display:flex;height:30px;border-radius:8px;overflow:hidden;font-size:12px}
.seg{display:flex;align-items:center;justify-content:center;color:#0b0e14;font-weight:700}
.seg.home{background:var(--home)}.seg.draw{background:var(--draw)}.seg.away{background:var(--away)}
.legend{display:flex;gap:14px;margin:7px 0 4px;font-size:12px;color:var(--mut)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px}
.dot.home{background:var(--home)}.dot.draw{background:var(--draw)}.dot.away{background:var(--away)}
.concl{margin-top:12px;font-size:13px;color:#c7cede;border-top:1px solid var(--line);padding-top:10px}
footer{margin-top:30px;color:var(--mut);font-size:12px;text-align:center;line-height:1.8}
"""


def render():
    data = json.load(open(IN_PATH, encoding="utf-8"))
    md1 = [m for m in data["matches"] if m["matchday"] == 1]
    cards = "\n".join(card(m) for m in md1)
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>球神谕 · 2026世界杯 第一轮 AI 分析结论</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>⚽ 球神谕 · 2026 世界杯 第一轮 AI 分析结论</h1>
<div class="tag">Dixon-Coles 模型概率 · 共 {len(md1)} 场 · 看球参考</div>
<div class="warn">
⚠️ <b>这是模型概率分析，不是投注建议、不是推单。</b><br>
• <b>"最可能"≠"最值得买"</b>：本页未对比竞彩赔率(SP)、未计算价值(EV)。热门的高概率早被赔率吃掉，<b>盲买热门长期必亏</b>。<br>
• 模型基于公开国际赛果，跨洲对阵存在不确定性，仅供看球参考。<br>
• 理性投注，未满 18 周岁禁止参与。本工具不代购、不承诺收益、不提供投注。
</div>
<div class="grid">{cards}</div>
<footer>球神谕 · 信息分析工具 · 第一轮模型结论 · 不构成任何投注建议</footer>
</div></body></html>"""
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    open(OUT_PATH, "w", encoding="utf-8").write(html)
    return OUT_PATH


if __name__ == "__main__":
    print("生成 ->", render())
