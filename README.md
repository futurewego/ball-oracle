# ball-oracle（球神谕）

面向中国球迷的 **2026 美加墨世界杯竞彩预测工具**。用一套进球分布模型（Dixon-Coles 双泊松）统一覆盖竞彩 5 大玩法，透明展示概率，**诚实不承诺赢**——帮你看懂概率、避开烂注、跟 AI 比准的娱乐工具。

> ⚠️ 本产品仅提供数据分析与概率参考，**不构成投注建议、不代购、不承诺收益**。理性投注，未满 18 周岁禁止使用。

## 定位

- 竞彩主流盘是公众资金驱动的"软盘"（返还率 ~86%、水位 14-16%），存在系统性偏差但水位厚。
- 价值不在"稳赢主流盘"，而在：抓公众偏差 + 冷门玩法（比分/半全场）+ 开盘早期 SP。
- 卖点是**透明 + 校准可验证 + 诚实**，区别于市面的黑盒推单号。

## 文档

- 产品设计：[`docs/superpowers/specs/2026-06-11-ball-oracle-design.md`](docs/superpowers/specs/2026-06-11-ball-oracle-design.md)
- 预测方案 v2.1：[`docs/superpowers/specs/2026-06-11-ticai-prediction-scheme.md`](docs/superpowers/specs/2026-06-11-ticai-prediction-scheme.md)

## 技术栈（规划）

- 前端：Next.js (App Router) + Tailwind，部署 Vercel
- 后端/数据：Supabase (Postgres + Auth + Realtime)
- 预测引擎：Python (Dixon-Coles 双泊松) + FastAPI
- LLM：Claude（数字 → 人话锐评，受控调 λ）

## 状态

设计与方案已成型（含 P0 数据/水位实测、完整性审查）。第一波 MVP：胜平负 + 总进球**概率区间展示**。
