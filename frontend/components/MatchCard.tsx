import type { MatchPrediction } from "@/lib/types";
import { ProbBar } from "./ProbBar";
import { GoalSpark } from "./GoalSpark";

export function MatchCard({ m }: { m: MatchPrediction }) {
  const scores = m.top_scores
    .slice(0, 3)
    .map(([k, v]) => `${k} ${(v * 100).toFixed(0)}%`)
    .join(" · ");
  return (
    <article className="card">
      <header>
        <span className="grp">组 {m.group} · 第{m.matchday}轮</span>
        <span className="date">{m.date}</span>
      </header>
      <h2>{m.home_cn} <small>vs</small> {m.away_cn}</h2>
      <div className="venue">
        {m.neutral ? "中立场" : "东道主主场"}　预期比分 λ {m.lam_home} - {m.lam_away}
      </div>
      <ProbBar spf={m.spf} homeCn={m.home_cn} awayCn={m.away_cn} />
      <div className="sub">总进球分布</div>
      <GoalSpark tg={m.total_goals} />
      <div className="sub">高概率比分　{scores}</div>
      <p className="summary">{m.summary}</p>
    </article>
  );
}
