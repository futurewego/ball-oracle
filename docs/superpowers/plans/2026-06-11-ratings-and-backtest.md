# λ估计（Dixon-Coles MLE）+ 校准回测 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从公开国际比赛数据用 Dixon-Coles 极大似然估计球队进攻/防守评分，产出任意对阵的 (λ_home, λ_away)；并在 2022 世界杯 + 2024 欧洲杯上做校准回测，量化模型概率准不准（Brier/LogLoss）。

**Architecture:** 新建 `ratings/` 包，与纯 `engine/` 解耦。`data` 取数→`model` 极大似然拟合评分→`lam` 评分映射为 λ→`engine` 出概率→`metrics`+`backtest` 校准评估。回测按**赛事粒度**拟合（赛前一次，无未来泄漏、可行），不逐场重拟合。

**Tech Stack:** Python 3.12，numpy + scipy（已装）做向量化似然与 L-BFGS 优化；engine 复用已有 Dixon-Coles 矩阵；pytest。

---

## 文件结构

- `ratings/__init__.py`
- `ratings/data.py` — 下载/解析 results.csv → `Match` 列表，按日期过滤
- `ratings/metrics.py` — Brier / LogLoss / 可靠性表（纯函数，先做、最易测）
- `ratings/model.py` — DC 负对数似然（向量化）+ `fit()` → `Ratings`
- `ratings/lam.py` — `Ratings` + 对阵 → (λ_home, λ_away)
- `ratings/backtest.py` — 赛事粒度回测 + 报告
- `tests/test_data.py` / `test_metrics.py` / `test_model.py` / `test_lam.py` / `test_backtest.py`
- `data/cache/` — 下载缓存（已在 .gitignore）

数据流：`data → model.fit → Ratings → lam.expected_goals → engine.score_matrix → outcome_1x2 → metrics`。

---

### Task 1: 数据加载

**Files:**
- Create: `ratings/__init__.py`（空）
- Create: `ratings/data.py`
- Test: `tests/test_data.py`

- [ ] **Step 1: 写失败测试**

`tests/test_data.py`：
```python
import datetime
from ratings.data import Match, load_matches, filter_before, ensure_dataset


def test_dataset_loads_many_matches():
    path = ensure_dataset()
    matches = load_matches(path)
    assert len(matches) > 40000


def test_match_fields_typed():
    matches = load_matches(ensure_dataset())
    m = matches[0]
    assert isinstance(m, Match)
    assert isinstance(m.date, datetime.date)
    assert isinstance(m.home_score, int) and isinstance(m.away_score, int)
    assert isinstance(m.neutral, bool)


def test_filter_before_excludes_later():
    matches = load_matches(ensure_dataset())
    cutoff = datetime.date(2000, 1, 1)
    before = filter_before(matches, cutoff)
    assert before and all(m.date < cutoff for m in before)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_data.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'ratings.data'`

- [ ] **Step 3: 实现**

`ratings/__init__.py`：
```python
```

`ratings/data.py`：
```python
import csv
import datetime
import os
import urllib.request
from dataclasses import dataclass

DATASET_URL = (
    "https://raw.githubusercontent.com/martj42/"
    "international_results/master/results.csv"
)
CACHE_PATH = os.path.join("data", "cache", "results.csv")


@dataclass(frozen=True)
class Match:
    date: datetime.date
    home: str
    away: str
    home_score: int
    away_score: int
    neutral: bool


def ensure_dataset(path: str = CACHE_PATH) -> str:
    """下载数据集到本地缓存（已存在则跳过）。返回路径。"""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(DATASET_URL, path)
    return path


def load_matches(path: str) -> list[Match]:
    """解析 results.csv，跳过缺分数的行。"""
    matches = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["home_score"] or not row["away_score"]:
                continue
            matches.append(
                Match(
                    date=datetime.date.fromisoformat(row["date"]),
                    home=row["home_team"],
                    away=row["away_team"],
                    home_score=int(row["home_score"]),
                    away_score=int(row["away_score"]),
                    neutral=row["neutral"].strip().lower() == "true",
                )
            )
    return matches


def filter_before(matches: list[Match], cutoff: datetime.date) -> list[Match]:
    return [m for m in matches if m.date < cutoff]
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_data.py -q`
Expected: `3 passed`

- [ ] **Step 5: 提交**

```bash
git add ratings/__init__.py ratings/data.py tests/test_data.py
git commit -m "feat: 国际比赛数据加载"
```

---

### Task 2: 校准指标（Brier / LogLoss / 可靠性）

**Files:**
- Create: `ratings/metrics.py`
- Test: `tests/test_metrics.py`

- [ ] **Step 1: 写失败测试**

`tests/test_metrics.py`：
```python
import math
from ratings.metrics import brier_score, log_loss, reliability_table

CLASSES = ("home", "draw", "away")


def test_brier_perfect_is_zero():
    probs = [{"home": 1.0, "draw": 0.0, "away": 0.0}]
    assert brier_score(probs, ["home"]) == 0.0


def test_brier_known_value():
    # 均匀预测、真值 home：sum((1/3-1)^2 + (1/3)^2 + (1/3)^2) = 2/3
    probs = [{"home": 1 / 3, "draw": 1 / 3, "away": 1 / 3}]
    assert math.isclose(brier_score(probs, ["home"]), 2 / 3, rel_tol=1e-9)


def test_log_loss_perfect_near_zero():
    probs = [{"home": 0.999999, "draw": 0.0000005, "away": 0.0000005}]
    assert log_loss(probs, ["home"]) < 1e-5


def test_reliability_table_bins_counts():
    probs = [{"home": 0.9, "draw": 0.05, "away": 0.05},
             {"home": 0.1, "draw": 0.8, "away": 0.1}]
    table = reliability_table(probs, ["home", "draw"], n_bins=10)
    total = sum(row["count"] for row in table)
    assert total == 6  # 2 场 × 3 类
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_metrics.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'ratings.metrics'`

- [ ] **Step 3: 实现**

`ratings/metrics.py`：
```python
import math

CLASSES = ("home", "draw", "away")


def brier_score(probs: list[dict], outcomes: list[str]) -> float:
    """多分类 Brier：每场 Σ_k (p_k − y_k)^2 的均值（越低越好）。"""
    total = 0.0
    for p, y in zip(probs, outcomes):
        total += sum((p[k] - (1.0 if k == y else 0.0)) ** 2 for k in CLASSES)
    return total / len(probs)


def log_loss(probs: list[dict], outcomes: list[str], eps: float = 1e-15) -> float:
    """对数损失：−mean(log p_真值)（越低越好）。"""
    total = 0.0
    for p, y in zip(probs, outcomes):
        total += -math.log(min(max(p[y], eps), 1.0))
    return total / len(probs)


def reliability_table(probs: list[dict], outcomes: list[str],
                      n_bins: int = 10) -> list[dict]:
    """把所有 (类预测概率, 是否命中) 摊平后按概率分箱，比较预测均值 vs 经验频率。"""
    bins = [{"pred_sum": 0.0, "hit": 0, "count": 0} for _ in range(n_bins)]
    for p, y in zip(probs, outcomes):
        for k in CLASSES:
            pk = p[k]
            idx = min(int(pk * n_bins), n_bins - 1)
            bins[idx]["pred_sum"] += pk
            bins[idx]["hit"] += 1 if k == y else 0
            bins[idx]["count"] += 1
    table = []
    for i, b in enumerate(bins):
        c = b["count"]
        table.append({
            "bin": i,
            "pred_mean": b["pred_sum"] / c if c else 0.0,
            "emp_freq": b["hit"] / c if c else 0.0,
            "count": c,
        })
    return table
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_metrics.py -q`
Expected: `4 passed`

- [ ] **Step 5: 提交**

```bash
git add ratings/metrics.py tests/test_metrics.py
git commit -m "feat: 校准指标 Brier/LogLoss/可靠性表"
```

---

### Task 3: Dixon-Coles 极大似然拟合

**Files:**
- Create: `ratings/model.py`
- Test: `tests/test_model.py`

- [ ] **Step 1: 写失败测试（小合成数据，快）**

`tests/test_model.py`：
```python
import datetime
import math
from ratings.data import Match
from ratings.model import fit, Ratings


def _synthetic():
    # A 对 B 长期大胜：A 应得更高 attack
    base = datetime.date(2020, 1, 1)
    matches = []
    for k in range(40):
        d = base + datetime.timedelta(days=k * 7)
        matches.append(Match(d, "A", "B", 3, 0, neutral=True))
        matches.append(Match(d, "B", "A", 0, 2, neutral=True))
    return matches


def test_fit_returns_ratings():
    r = fit(_synthetic(), half_life_days=3650)
    assert isinstance(r, Ratings)
    assert "A" in r.attack and "B" in r.attack


def test_stronger_team_has_higher_attack():
    r = fit(_synthetic(), half_life_days=3650)
    assert r.attack["A"] > r.attack["B"]


def test_attack_mean_centered():
    r = fit(_synthetic(), half_life_days=3650)
    mean_a = sum(r.attack.values()) / len(r.attack)
    assert abs(mean_a) < 1e-3
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_model.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'ratings.model'`

- [ ] **Step 3: 实现**

`ratings/model.py`：
```python
import datetime
import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

from ratings.data import Match


@dataclass
class Ratings:
    attack: dict        # team -> float（均值约 0）
    defense: dict       # team -> float
    home_adv: float
    rho: float


def _dc_log_tau(hs, as_, lam_h, lam_a, rho):
    """Dixon-Coles 低分修正的对数（向量化）。仅低分单元 ≠0。"""
    out = np.zeros_like(lam_h)
    m00 = (hs == 0) & (as_ == 0)
    m01 = (hs == 0) & (as_ == 1)
    m10 = (hs == 1) & (as_ == 0)
    m11 = (hs == 1) & (as_ == 1)
    out[m00] = np.log(np.maximum(1 - lam_h[m00] * lam_a[m00] * rho, 1e-12))
    out[m01] = np.log(np.maximum(1 + lam_h[m01] * rho, 1e-12))
    out[m10] = np.log(np.maximum(1 + lam_a[m10] * rho, 1e-12))
    out[m11] = np.log(np.maximum(1 - rho, 1e-12))
    return out


def fit(matches: list[Match], half_life_days: float = 730.0,
        l2: float = 1e-3, max_iter: int = 200) -> Ratings:
    """对一批比赛做时间加权的 Dixon-Coles 极大似然，返回评分。"""
    teams = sorted({m.home for m in matches} | {m.away for m in matches})
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)

    hi = np.array([idx[m.home] for m in matches])
    ai = np.array([idx[m.away] for m in matches])
    hs = np.array([m.home_score for m in matches], dtype=float)
    as_ = np.array([m.away_score for m in matches], dtype=float)
    neutral = np.array([m.neutral for m in matches], dtype=bool)

    t_max = max(m.date for m in matches)
    age = np.array([(t_max - m.date).days for m in matches], dtype=float)
    xi = math.log(2.0) / half_life_days
    w = np.exp(-xi * age)

    lg_hs = gammaln(hs + 1.0)
    lg_as = gammaln(as_ + 1.0)

    def unpack(p):
        attack = p[:n]
        defense = p[n:2 * n]
        home_adv = p[2 * n]
        rho = p[2 * n + 1]
        return attack, defense, home_adv, rho

    def nll(p):
        attack, defense, home_adv, rho = unpack(p)
        log_lh = attack[hi] - defense[ai] + np.where(neutral, 0.0, home_adv)
        log_la = attack[ai] - defense[hi]
        lam_h = np.exp(np.clip(log_lh, -10, 4))
        lam_a = np.exp(np.clip(log_la, -10, 4))
        ll_h = hs * np.log(lam_h) - lam_h - lg_hs
        ll_a = as_ * np.log(lam_a) - lam_a - lg_as
        ll_tau = _dc_log_tau(hs, as_, lam_h, lam_a, rho)
        ll = w * (ll_h + ll_a + ll_tau)
        penalty = l2 * (attack.mean() ** 2 * n + np.sum(attack ** 2)
                        + np.sum(defense ** 2))
        return -(ll.sum()) + penalty

    x0 = np.zeros(2 * n + 2)
    x0[2 * n] = 0.25   # home_adv 初值
    x0[2 * n + 1] = -0.05  # rho 初值
    bounds = [(-3, 3)] * (2 * n) + [(-1, 1), (-0.2, 0.2)]
    res = minimize(nll, x0, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": max_iter})

    attack, defense, home_adv, rho = unpack(res.x)
    attack = attack - attack.mean()  # 强制中心化
    return Ratings(
        attack={t: float(attack[idx[t]]) for t in teams},
        defense={t: float(defense[idx[t]]) for t in teams},
        home_adv=float(home_adv),
        rho=float(rho),
    )
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_model.py -q`
Expected: `3 passed`

- [ ] **Step 5: 提交**

```bash
git add ratings/model.py tests/test_model.py
git commit -m "feat: Dixon-Coles 极大似然评分拟合"
```

---

### Task 4: 评分 → λ

**Files:**
- Create: `ratings/lam.py`
- Test: `tests/test_lam.py`

- [ ] **Step 1: 写失败测试**

`tests/test_lam.py`：
```python
from ratings.model import Ratings
from ratings.lam import expected_goals


def _ratings():
    return Ratings(
        attack={"A": 0.5, "B": -0.5},
        defense={"A": 0.3, "B": -0.3},
        home_adv=0.25,
        rho=-0.05,
    )


def test_stronger_team_higher_lambda():
    lh, la = expected_goals(_ratings(), "A", "B", neutral=True)
    assert lh > la


def test_home_advantage_applied_when_not_neutral():
    lh_n, _ = expected_goals(_ratings(), "A", "B", neutral=True)
    lh_h, _ = expected_goals(_ratings(), "A", "B", neutral=False)
    assert lh_h > lh_n  # 非中立场主队 λ 更高


def test_unknown_team_uses_average():
    lh, la = expected_goals(_ratings(), "A", "UNKNOWN", neutral=True)
    assert lh > 0 and la > 0  # 未知队按均值(0)处理，不崩
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_lam.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'ratings.lam'`

- [ ] **Step 3: 实现**

`ratings/lam.py`：
```python
import math
from ratings.model import Ratings


def expected_goals(ratings: Ratings, home: str, away: str,
                   neutral: bool = False) -> tuple[float, float]:
    """评分映射为 (λ_home, λ_away)。未知队按均值 0 处理。"""
    a_home = ratings.attack.get(home, 0.0)
    a_away = ratings.attack.get(away, 0.0)
    d_home = ratings.defense.get(home, 0.0)
    d_away = ratings.defense.get(away, 0.0)
    adv = 0.0 if neutral else ratings.home_adv
    lam_h = math.exp(a_home - d_away + adv)
    lam_a = math.exp(a_away - d_home)
    return lam_h, lam_a
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_lam.py -q`
Expected: `3 passed`

- [ ] **Step 5: 提交**

```bash
git add ratings/lam.py tests/test_lam.py
git commit -m "feat: 评分映射为 λ"
```

---

### Task 5: 回测预测函数

**Files:**
- Create: `ratings/backtest.py`
- Test: `tests/test_backtest.py`

- [ ] **Step 1: 写失败测试**

`tests/test_backtest.py`：
```python
import math
from ratings.model import Ratings
from ratings.backtest import predict_1x2, outcome_of


def _ratings():
    return Ratings(attack={"A": 0.5, "B": -0.5},
                   defense={"A": 0.3, "B": -0.3}, home_adv=0.25, rho=-0.05)


def test_predict_1x2_sums_to_one():
    p = predict_1x2(_ratings(), "A", "B", neutral=True)
    assert math.isclose(p["home"] + p["draw"] + p["away"], 1.0, rel_tol=1e-9)


def test_predict_stronger_home_more_likely():
    p = predict_1x2(_ratings(), "A", "B", neutral=True)
    assert p["home"] > p["away"]


def test_outcome_of():
    assert outcome_of(2, 0) == "home"
    assert outcome_of(1, 1) == "draw"
    assert outcome_of(0, 3) == "away"
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_backtest.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'ratings.backtest'`

- [ ] **Step 3: 实现**

`ratings/backtest.py`：
```python
from ratings.model import Ratings
from ratings.lam import expected_goals
from engine.scoreline import score_matrix
from engine.markets import outcome_1x2


def outcome_of(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home"
    if home_score == away_score:
        return "draw"
    return "away"


def predict_1x2(ratings: Ratings, home: str, away: str,
                neutral: bool = False) -> dict:
    lam_h, lam_a = expected_goals(ratings, home, away, neutral)
    m = score_matrix(lam_h, lam_a, rho=ratings.rho)
    return outcome_1x2(m)
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_backtest.py -q`
Expected: `3 passed`

- [ ] **Step 5: 提交**

```bash
git add ratings/backtest.py tests/test_backtest.py
git commit -m "feat: 回测预测函数"
```

---

### Task 6: 回测脚本（赛事粒度拟合 + 报告）

**Files:**
- Modify: `ratings/backtest.py`（追加 run + main）
- Test: 手动运行（真实数据，非单测）

- [ ] **Step 1: 追加回测主流程**

在 `ratings/backtest.py` 追加：
```python
import datetime
from ratings.data import ensure_dataset, load_matches, filter_before
from ratings.model import fit
from ratings.metrics import brier_score, log_loss


# (赛事名, 开赛日, 结束日, 是否中立场)
TOURNAMENTS = [
    ("World Cup 2022", datetime.date(2022, 11, 20), datetime.date(2022, 12, 18), True),
    ("Euro 2024", datetime.date(2024, 6, 14), datetime.date(2024, 7, 14), True),
]


def run_tournament(all_matches, name, start, end, neutral, train_years=12):
    train_cut = start
    train_start = datetime.date(start.year - train_years, 1, 1)
    train = [m for m in all_matches if train_start <= m.date < train_cut]
    test = [m for m in all_matches if start <= m.date <= end]
    ratings = fit(train, half_life_days=730.0)
    probs, outs = [], []
    for m in test:
        probs.append(predict_1x2(ratings, m.home, m.away, neutral=neutral))
        outs.append(outcome_of(m.home_score, m.away_score))
    return {
        "name": name,
        "n_train": len(train),
        "n_test": len(test),
        "brier": brier_score(probs, outs),
        "log_loss": log_loss(probs, outs),
    }


def main():
    matches = load_matches(ensure_dataset())
    for name, start, end, neutral in TOURNAMENTS:
        r = run_tournament(matches, name, start, end, neutral)
        print(f"{r['name']}: 训练 {r['n_train']} 场, 测试 {r['n_test']} 场, "
              f"Brier={r['brier']:.4f}, LogLoss={r['log_loss']:.4f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行回测，记录真实 Brier/LogLoss**

Run: `python -m ratings.backtest`
Expected: 打印两届赛事的 Brier 与 LogLoss。**正确基准（多分类 Brier=Σ_k(p_k−y_k)²，范围0~2）**：均匀瞎猜 Brier=0.667 / LogLoss=1.099。判读：明显低于瞎猜 = 有真实信号；强模型/博彩量级约 0.55~0.62。真正的对标是竞彩 SP 隐含概率在同批比赛上的 Brier（需 SP 数据，后续做）——跑赢瞎猜≠跑赢市场。

> ⚠️ 历史记录：本计划初稿误写"Brier<0.22"，那是混淆了别的度量约定。三分类求和 Brier 下，0.22 实际上不可达；正确锚点见上。

- [ ] **Step 3: 提交**

```bash
git add ratings/backtest.py
git commit -m "feat: 赛事粒度校准回测脚本"
```

---

## 完成判据

- `python -m pytest -q` 全绿（含 engine 的 25 + ratings 新增约 16）。
- `python -m ratings.backtest` 输出 2022WC / 2024Euro 的 Brier 与 LogLoss。
- **决策门（已校正基准）**：多分类 Brier 明显低于瞎猜 0.667 → 模型有真实信号、可进数据层 + 概率展示；接近或高于 0.667 → 回炉（时间衰减、训练窗、洲际收缩、§9.4 物理特征）。
- **实测结果（2026-06-11）**：Euro2024 Brier=0.544 / LogLoss=0.919；WC2022 Brier=0.601 / LogLoss=1.040。两届均胜瞎猜，Euro 接近市场级。**决策门通过**（WC2022 偏弱因该届冷门极多）。下一步真正对标竞彩 SP（需 SP 数据）。

## 后续（不在本计划）

- 模型不达标时的增强：洲际层级收缩、§9.4 海拔/高温/旅行/东道主特征、每赛日贝叶斯更新。
- 价值回测（需历史竞彩 SP，依赖数据层）：去水位 → EV → CLV 跟踪。
- 数据接入（聚合 API + Supabase）、Web 概率展示。
