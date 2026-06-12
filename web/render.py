"""把 build/predictions.json 渲染成自包含静态 HTML 产品页（可直接浏览器打开）。

这是第一波 MVP 的"脸"：概率展示 + 诚实定位 + 免责。无 SP/价值（第二波）。
"""
import json
import os

IN_PATH = os.path.join("build", "predictions.json")
OUT_PATH = os.path.join("web", "index.html")

DISCLAIMER = ("仅供数据分析参考，不构成投注建议。理性投注，未满 18 周岁禁止参与。"
              "模型概率 ≠ 中奖概率，竞彩长期返还率＜100%，亏损为常态。")


def _spf_bar(spf, home_cn, away_cn):
    h, d, a = spf["home"], spf["draw"], spf["away"]
    return f"""
      <div class="bar">
        <div class="seg home" style="width:{h*100:.1f}%"><span>{h*100:.0f}%</span></div>
        <div class="seg draw" style="width:{d*100:.1f}%"><span>{d*100:.0f}%</span></div>
        <div class="seg away" style="width:{a*100:.1f}%"><span>{a*100:.0f}%</span></div>
      </div>
      <div class="legend">
        <span><i class="dot home"></i>{home_cn}胜</span>
        <span><i class="dot draw"></i>平</span>
        <span><i class="dot away"></i>{away_cn}胜</span>
      </div>"""


def _tg_spark(tg):
    order = ["0", "1", "2", "3", "4", "5", "6", "7+"]
    mx = max(tg.values()) or 1
    bars = "".join(
        f'<div class="tg"><div class="tgfill" style="height:{tg[k]/mx*100:.0f}%"></div>'
        f'<div class="tglab">{k}</div></div>' for k in order)
    return f'<div class="tgrow">{bars}</div>'


def _card(m):
    scores = " · ".join(f'{k} <b>{v*100:.0f}%</b>' for k, v in m["top_scores"][:3])
    return f"""
    <article class="card">
      <header>
        <span class="grp">组 {m['group']} · 第{m['matchday']}轮</span>
        <span class="date">{m['date']}</span>
      </header>
      <h2>{m['home_cn']} <small>vs</small> {m['away_cn']}</h2>
      <div class="venue">{'东道主主场' if not m['neutral'] else '中立场'}
        　预期比分 λ {m['lam_home']} - {m['lam_away']}</div>
      {_spf_bar(m['spf'], m['home_cn'], m['away_cn'])}
      <div class="sub">总进球分布</div>
      {_tg_spark(m['total_goals'])}
      <div class="sub">高概率比分　{scores}</div>
      <p class="summary">{m['summary']}</p>
    </article>"""


def render(in_path: str = IN_PATH, out_path: str = OUT_PATH) -> str:
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    cards = "\n".join(_card(m) for m in data["matches"])
    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>球神谕 · 2026世界杯AI预测</title>
<style>
  :root{{--bg:#0b0e14;--card:#141925;--line:#222a3a;--home:#3ea6ff;--draw:#8b93a7;--away:#ff5d73;--txt:#e6e9f0;--mut:#8b93a7}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--txt);font-family:"PingFang SC",-apple-system,system-ui,sans-serif;line-height:1.5}}
  .wrap{{max-width:1100px;margin:0 auto;padding:24px 16px 64px}}
  .top h1{{font-size:24px;letter-spacing:1px}}
  .top .tag{{color:var(--mut);font-size:13px;margin-top:4px}}
  .warn{{margin:16px 0;padding:12px 14px;border:1px solid #3a2a2a;background:#1c1414;border-radius:10px;color:#ffb4b4;font-size:13px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;margin-top:18px}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}}
  .card header{{display:flex;justify-content:space-between;color:var(--mut);font-size:12px}}
  .grp{{background:#1d2740;color:#9fc0ff;padding:1px 8px;border-radius:20px}}
  .card h2{{font-size:19px;margin:8px 0 2px}} .card h2 small{{color:var(--mut);font-weight:400;font-size:13px}}
  .venue{{color:var(--mut);font-size:12px;margin-bottom:12px}}
  .bar{{display:flex;height:30px;border-radius:8px;overflow:hidden;font-size:12px}}
  .seg{{display:flex;align-items:center;justify-content:center;color:#0b0e14;font-weight:700}}
  .seg.home{{background:var(--home)}} .seg.draw{{background:var(--draw)}} .seg.away{{background:var(--away)}}
  .seg span{{opacity:.95}}
  .legend{{display:flex;gap:14px;margin:7px 0 4px;font-size:12px;color:var(--mut)}}
  .dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px}}
  .dot.home{{background:var(--home)}} .dot.draw{{background:var(--draw)}} .dot.away{{background:var(--away)}}
  .sub{{color:var(--mut);font-size:12px;margin:12px 0 6px}}
  .tgrow{{display:flex;align-items:flex-end;gap:5px;height:46px}}
  .tg{{flex:1;text-align:center;display:flex;flex-direction:column;justify-content:flex-end;height:34px}}
  .tgfill{{background:linear-gradient(#5fb0ff,#2b6fd6);border-radius:3px 3px 0 0;min-height:3px}}
  .tglab{{font-size:10px;color:var(--mut);margin-top:3px}}
  .summary{{margin-top:12px;font-size:13px;color:#c7cede;border-top:1px solid var(--line);padding-top:10px}}
  footer{{margin-top:30px;color:var(--mut);font-size:12px;text-align:center;line-height:1.8}}
</style></head>
<body><div class="wrap">
  <div class="top">
    <h1>⚽ 球神谕 · 2026 世界杯 AI 预测</h1>
    <div class="tag">{data['model']} ｜ {data['note']}　·　不承诺赢，只帮你看懂概率</div>
  </div>
  <div class="warn">⚠️ {DISCLAIMER}</div>
  <div class="grid">
    {cards}
  </div>
  <footer>
    球神谕为信息分析工具，不代购、不承诺收益、不提供投注。<br>
    模型基于公开国际赛果(Dixon-Coles)，含洲际跨洲校正；预测存在不确定性，请独立判断。
  </footer>
</div></body></html>"""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


if __name__ == "__main__":
    print("生成页面 ->", render())
