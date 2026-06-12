import { getPredictions, groupedByGroup } from "@/lib/data";
import { MatchCard } from "@/components/MatchCard";

const DISCLAIMER =
  "仅供数据分析参考，不构成投注建议。理性投注，未满 18 周岁禁止参与。" +
  "模型概率 ≠ 中奖概率，竞彩长期返还率＜100%，亏损为常态。";

export default function Home() {
  const data = getPredictions();
  const groups = groupedByGroup();
  const groupKeys = Object.keys(groups).sort();

  return (
    <div className="wrap">
      <div className="top">
        <h1>⚽ 球神谕 · 2026 世界杯 AI 预测</h1>
        <div className="tag">
          {data.model} ｜ {data.note}　·　不承诺赢，只帮你看懂概率
        </div>
      </div>

      <div className="warn">⚠️ {DISCLAIMER}</div>

      <div className="pk">
        🏆 用户 PK / 命中率排行：即将上线（需接入 Supabase 登录与数据库）——
        你与 AI 同台预测，比谁更准。
      </div>

      {groupKeys.map((g) => (
        <section key={g}>
          <div className="grouphead">小组 {g}</div>
          <div className="grid">
            {groups[g].map((m, i) => (
              <MatchCard m={m} key={`${g}-${i}`} />
            ))}
          </div>
        </section>
      ))}

      <footer>
        球神谕为信息分析工具，不代购、不承诺收益、不提供投注。
        <br />
        模型基于公开国际赛果(Dixon-Coles)，含洲际跨洲校正；预测存在不确定性，请独立判断。
      </footer>
    </div>
  );
}
