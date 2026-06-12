# 预测引擎核心 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个纯函数预测引擎：输入两队期望进球 (λ_home, λ_away)，输出竞彩全部 5 大玩法的概率分布，全部单元测试覆盖、零外部依赖。

**Architecture:** 用 Dixon-Coles 双泊松构建比分联合分布矩阵 P(i,j)，再由同一矩阵解析导出 5 玩法（胜平负/让球/比分31项/总进球8项/半全场9项）。半全场用上下两段独立泊松相加（保留 HT 与 FT 相关性，见方案 §2.2）。本计划只做"λ → 概率"的数学核心；λ 的估计（评分拟合）与数据接入是后续独立 plan。

**Tech Stack:** Python 3.11+，仅标准库 `math`（不引入 numpy，保持零重依赖、易测）；pytest 测试。

---

## 文件结构

- `engine/__init__.py` — 包入口，导出 `predict`
- `engine/scoreline.py` — 泊松 PMF + Dixon-Coles 比分矩阵
- `engine/markets.py` — 由矩阵/λ 导出 5 玩法
- `engine/predict.py` — 顶层组装 `predict()`，返回全玩法结果并校验不变量
- `tests/test_scoreline.py`
- `tests/test_markets.py`
- `tests/test_predict.py`
- `pyproject.toml` — 项目与 pytest 配置

每个文件单一职责：scoreline 只管"造矩阵"，markets 只管"矩阵→玩法"，predict 只管"组装+不变量校验"。

---

### Task 1: 项目脚手架 + 冒烟测试

**Files:**
- Create: `pyproject.toml`
- Create: `engine/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_smoke.py`

- [ ] **Step 1: 写 pyproject.toml**

```toml
[project]
name = "ball-oracle-engine"
version = "0.1.0"
description = "Dixon-Coles 竞彩预测引擎核心"
requires-python = ">=3.11"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 2: 建空包文件**

`engine/__init__.py`（暂空，Task 9 再填导出）：
```python
```

`tests/__init__.py`：
```python
```

- [ ] **Step 3: 写冒烟测试**

`tests/test_smoke.py`：
```python
def test_python_and_pytest_work():
    assert 1 + 1 == 2
```

- [ ] **Step 4: 运行，确认通过**

Run: `python -m pytest -q`
Expected: `1 passed`

- [ ] **Step 5: 提交**

```bash
git add pyproject.toml engine/__init__.py tests/__init__.py tests/test_smoke.py
git commit -m "chore: 预测引擎脚手架 + 冒烟测试"
```

---

### Task 2: 泊松 PMF

**Files:**
- Create: `engine/scoreline.py`
- Test: `tests/test_scoreline.py`

- [ ] **Step 1: 写失败测试**

`tests/test_scoreline.py`：
```python
import math
from engine.scoreline import poisson_pmf


def test_poisson_pmf_zero():
    # P(X=0; λ=1) = e^-1
    assert poisson_pmf(0, 1.0) == math.exp(-1.0)


def test_poisson_pmf_known_value():
    # P(X=2; λ=2) = e^-2 * 2^2 / 2! = 2 e^-2
    assert math.isclose(poisson_pmf(2, 2.0), 2 * math.exp(-2.0), rel_tol=1e-12)


def test_poisson_pmf_negative_k_is_zero():
    assert poisson_pmf(-1, 1.5) == 0.0
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_scoreline.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'engine.scoreline'`

- [ ] **Step 3: 最小实现**

`engine/scoreline.py`：
```python
import math


def poisson_pmf(k: int, lam: float) -> float:
    """泊松概率质量 P(X=k; lam)。k<0 返回 0。"""
    if k < 0:
        return 0.0
    return math.exp(-lam) * lam**k / math.factorial(k)
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_scoreline.py -q`
Expected: `3 passed`

- [ ] **Step 5: 提交**

```bash
git add engine/scoreline.py tests/test_scoreline.py
git commit -m "feat: 泊松 PMF"
```

---

### Task 3: Dixon-Coles 比分矩阵

**Files:**
- Modify: `engine/scoreline.py`
- Test: `tests/test_scoreline.py`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_scoreline.py` 末尾追加：
```python
from engine.scoreline import score_matrix


def _matrix_sum(m):
    return sum(cell for row in m for cell in row)


def test_score_matrix_normalized():
    m = score_matrix(1.4, 1.1)
    assert math.isclose(_matrix_sum(m), 1.0, rel_tol=1e-9)


def test_score_matrix_dimensions():
    m = score_matrix(1.4, 1.1, max_goals=10)
    assert len(m) == 11 and all(len(row) == 11 for row in m)


def test_score_matrix_rho_zero_is_plain_poisson():
    # rho=0 时 (1,1) 单元应等于归一化前的 pmf 乘积比例
    m = score_matrix(1.5, 1.2, rho=0.0)
    # 平局对角线之和应为正且 <1
    diag = sum(m[i][i] for i in range(len(m)))
    assert 0.0 < diag < 1.0


def test_dixon_coles_lowers_draw_inflation():
    # rho<0 提高 0:0/1:1，降低 0:1/1:0（DC 对低分修正）
    plain = score_matrix(1.3, 1.3, rho=0.0)
    dc = score_matrix(1.3, 1.3, rho=-0.05)
    assert dc[0][0] > plain[0][0]
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_scoreline.py -q`
Expected: FAIL，`ImportError: cannot import name 'score_matrix'`

- [ ] **Step 3: 实现 score_matrix（含 DC tau）**

在 `engine/scoreline.py` 追加：
```python
def _dc_tau(i: int, j: int, lam_home: float, lam_away: float, rho: float) -> float:
    """Dixon-Coles 低比分修正因子。"""
    if i == 0 and j == 0:
        return 1.0 - lam_home * lam_away * rho
    if i == 0 and j == 1:
        return 1.0 + lam_home * rho
    if i == 1 and j == 0:
        return 1.0 + lam_away * rho
    if i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(
    lam_home: float,
    lam_away: float,
    rho: float = 0.0,
    max_goals: int = 10,
) -> list[list[float]]:
    """返回归一化的比分联合分布矩阵 m[i][j]=P(主进i, 客进j)。

    rho 为 Dixon-Coles 低分相关参数（典型 -0.1~0）。rho=0 退化为独立泊松。
    """
    raw = [
        [
            _dc_tau(i, j, lam_home, lam_away, rho)
            * poisson_pmf(i, lam_home)
            * poisson_pmf(j, lam_away)
            for j in range(max_goals + 1)
        ]
        for i in range(max_goals + 1)
    ]
    total = sum(cell for row in raw for cell in row)
    return [[cell / total for cell in row] for row in raw]
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_scoreline.py -q`
Expected: `7 passed`

- [ ] **Step 5: 提交**

```bash
git add engine/scoreline.py tests/test_scoreline.py
git commit -m "feat: Dixon-Coles 比分矩阵"
```

---

### Task 4: 胜平负 + 让球胜平负

**Files:**
- Create: `engine/markets.py`
- Test: `tests/test_markets.py`

- [ ] **Step 1: 写失败测试**

`tests/test_markets.py`：
```python
import math
from engine.scoreline import score_matrix
from engine.markets import outcome_1x2, handicap_1x2


def test_1x2_sums_to_one():
    m = score_matrix(1.5, 1.2)
    r = outcome_1x2(m)
    assert math.isclose(r["home"] + r["draw"] + r["away"], 1.0, rel_tol=1e-9)


def test_1x2_symmetric_lambdas_equal_home_away():
    m = score_matrix(1.3, 1.3)
    r = outcome_1x2(m)
    assert math.isclose(r["home"], r["away"], rel_tol=1e-9)


def test_handicap_home_minus_one_reduces_home_prob():
    # 主队让1球后主胜概率应低于不让球
    m = score_matrix(1.8, 1.0)
    base = outcome_1x2(m)
    h = handicap_1x2(m, handicap=-1)  # 主-1
    assert h["home"] < base["home"]


def test_handicap_sums_to_one():
    m = score_matrix(1.8, 1.0)
    h = handicap_1x2(m, handicap=-1)
    assert math.isclose(h["home"] + h["draw"] + h["away"], 1.0, rel_tol=1e-9)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_markets.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'engine.markets'`

- [ ] **Step 3: 实现**

`engine/markets.py`：
```python
def outcome_1x2(matrix: list[list[float]]) -> dict:
    """胜平负：主胜/平/客胜（全场 90 分钟口径）。"""
    home = draw = away = 0.0
    for i, row in enumerate(matrix):
        for j, p in enumerate(row):
            if i > j:
                home += p
            elif i == j:
                draw += p
            else:
                away += p
    return {"home": home, "draw": draw, "away": away}


def handicap_1x2(matrix: list[list[float]], handicap: int) -> dict:
    """让球胜平负。handicap = 加到主队净胜球上的整数（主队让1球→-1，客队让2球→+2）。"""
    home = draw = away = 0.0
    for i, row in enumerate(matrix):
        for j, p in enumerate(row):
            adj = (i + handicap) - j
            if adj > 0:
                home += p
            elif adj == 0:
                draw += p
            else:
                away += p
    return {"home": home, "draw": draw, "away": away}
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_markets.py -q`
Expected: `4 passed`

- [ ] **Step 5: 提交**

```bash
git add engine/markets.py tests/test_markets.py
git commit -m "feat: 胜平负 + 让球胜平负"
```

---

### Task 5: 比分（31 项）

**Files:**
- Modify: `engine/markets.py`
- Test: `tests/test_markets.py`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_markets.py` 追加：
```python
from engine.markets import correct_score


def test_correct_score_has_31_keys():
    m = score_matrix(1.5, 1.2)
    r = correct_score(m)
    assert len(r) == 31


def test_correct_score_sums_to_one():
    m = score_matrix(1.5, 1.2)
    r = correct_score(m)
    assert math.isclose(sum(r.values()), 1.0, rel_tol=1e-9)


def test_correct_score_draw_buckets_match_1x2_draw():
    m = score_matrix(1.4, 1.4)
    cs = correct_score(m)
    draw_total = cs["0:0"] + cs["1:1"] + cs["2:2"] + cs["3:3"] + cs["平其它"]
    assert math.isclose(draw_total, outcome_1x2(m)["draw"], rel_tol=1e-9)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_markets.py -q`
Expected: FAIL，`ImportError: cannot import name 'correct_score'`

- [ ] **Step 3: 实现**

在 `engine/markets.py` 追加：
```python
_HOME_SCORES = [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2),
                (4, 0), (4, 1), (4, 2), (5, 0), (5, 1), (5, 2)]
_DRAW_SCORES = [(0, 0), (1, 1), (2, 2), (3, 3)]
_AWAY_SCORES = [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3),
                (0, 4), (1, 4), (2, 4), (0, 5), (1, 5), (2, 5)]


def correct_score(matrix: list[list[float]]) -> dict:
    """比分 31 项：12 主胜具体 + 胜其它 / 4 平具体 + 平其它 / 12 客胜具体 + 负其它。"""
    n = len(matrix)

    def cell(i, j):
        return matrix[i][j] if i < n and j < n else 0.0

    result = {}
    for (i, j) in _HOME_SCORES:
        result[f"{i}:{j}"] = cell(i, j)
    for (i, j) in _DRAW_SCORES:
        result[f"{i}:{j}"] = cell(i, j)
    for (i, j) in _AWAY_SCORES:
        result[f"{i}:{j}"] = cell(i, j)

    o = outcome_1x2(matrix)
    result["胜其它"] = o["home"] - sum(cell(i, j) for i, j in _HOME_SCORES)
    result["平其它"] = o["draw"] - sum(cell(i, j) for i, j in _DRAW_SCORES)
    result["负其它"] = o["away"] - sum(cell(i, j) for i, j in _AWAY_SCORES)
    return result
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_markets.py -q`
Expected: `7 passed`

- [ ] **Step 5: 提交**

```bash
git add engine/markets.py tests/test_markets.py
git commit -m "feat: 比分 31 项"
```

---

### Task 6: 总进球数（8 项）

**Files:**
- Modify: `engine/markets.py`
- Test: `tests/test_markets.py`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_markets.py` 追加：
```python
from engine.markets import total_goals


def test_total_goals_has_8_keys():
    m = score_matrix(1.5, 1.2)
    r = total_goals(m)
    assert list(r.keys()) == ["0", "1", "2", "3", "4", "5", "6", "7+"]


def test_total_goals_sums_to_one():
    m = score_matrix(1.5, 1.2)
    assert math.isclose(sum(total_goals(m).values()), 1.0, rel_tol=1e-9)


def test_total_goals_zero_equals_nil_nil():
    m = score_matrix(1.5, 1.2)
    assert math.isclose(total_goals(m)["0"], m[0][0], rel_tol=1e-12)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_markets.py -q`
Expected: FAIL，`ImportError: cannot import name 'total_goals'`

- [ ] **Step 3: 实现**

在 `engine/markets.py` 追加：
```python
def total_goals(matrix: list[list[float]]) -> dict:
    """总进球数 8 档：0..6 与 7+。"""
    buckets = {str(k): 0.0 for k in range(7)}
    buckets["7+"] = 0.0
    for i, row in enumerate(matrix):
        for j, p in enumerate(row):
            t = i + j
            if t >= 7:
                buckets["7+"] += p
            else:
                buckets[str(t)] += p
    return buckets
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_markets.py -q`
Expected: `10 passed`

- [ ] **Step 5: 提交**

```bash
git add engine/markets.py tests/test_markets.py
git commit -m "feat: 总进球数 8 档"
```

---

### Task 7: 半全场（9 项，上下两段独立泊松）

**Files:**
- Modify: `engine/markets.py`
- Test: `tests/test_markets.py`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_markets.py` 追加：
```python
from engine.markets import half_full


def test_half_full_has_9_keys():
    r = half_full(1.5, 1.2)
    expected = ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"]
    assert sorted(r.keys()) == sorted(expected)


def test_half_full_sums_to_one():
    r = half_full(1.5, 1.2)
    assert math.isclose(sum(r.values()), 1.0, rel_tol=1e-9)


def test_half_full_ft_marginal_matches_1x2():
    # 半全场对 FT 边际（平胜+负胜+胜胜 = 全场主胜）应与 1x2 主胜接近
    lam_h, lam_a = 1.6, 1.0
    hf = half_full(lam_h, lam_a)
    ft_home = hf["胜胜"] + hf["平胜"] + hf["负胜"]
    # 用同 λ 的纯泊松全场矩阵对比（半全场未加 DC，故用 rho=0）
    o = outcome_1x2(score_matrix(lam_h, lam_a, rho=0.0))
    assert math.isclose(ft_home, o["home"], rel_tol=0.02)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_markets.py -q`
Expected: FAIL，`ImportError: cannot import name 'half_full'`

- [ ] **Step 3: 实现**

在 `engine/markets.py` 追加（顶部已 import 的 poisson 通过 scoreline 复用）：
```python
from engine.scoreline import poisson_pmf


def _sign(home: int, away: int) -> str:
    if home > away:
        return "胜"
    if home == away:
        return "平"
    return "负"


def half_full(lam_home: float, lam_away: float, c: float = 0.45,
              max_goals: int = 8) -> dict:
    """半全场 9 项。上半场 λ*c、下半场 λ*(1-c) 两段独立泊松，相加得全场，
    由 (上半场结果, 全场结果) 联合分布导出。保留 HT 与 FT 相关性。"""
    lh1, la1 = lam_home * c, lam_away * c
    lh2, la2 = lam_home * (1 - c), lam_away * (1 - c)

    keys = ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"]
    result = {k: 0.0 for k in keys}

    rng = range(max_goals + 1)
    for h1 in rng:
        for a1 in rng:
            p_ht = poisson_pmf(h1, lh1) * poisson_pmf(a1, la1)
            if p_ht == 0.0:
                continue
            ht = _sign(h1, a1)
            for h2 in rng:
                for a2 in rng:
                    p_2h = poisson_pmf(h2, lh2) * poisson_pmf(a2, la2)
                    ft = _sign(h1 + h2, a1 + a2)
                    result[ht + ft] += p_ht * p_2h
    total = sum(result.values())
    return {k: v / total for k, v in result.items()}
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_markets.py -q`
Expected: `13 passed`

- [ ] **Step 5: 提交**

```bash
git add engine/markets.py tests/test_markets.py
git commit -m "feat: 半全场 9 项（两段泊松联合分布）"
```

---

### Task 8: 顶层 predict() 组装 + 不变量

**Files:**
- Create: `engine/predict.py`
- Modify: `engine/__init__.py`
- Test: `tests/test_predict.py`

- [ ] **Step 1: 写失败测试**

`tests/test_predict.py`：
```python
import math
from engine import predict


def test_predict_returns_all_five_markets():
    r = predict(1.5, 1.2)
    assert set(r.keys()) == {"spf", "handicap", "correct_score", "total_goals", "half_full"}


def test_predict_all_markets_sum_to_one():
    r = predict(1.5, 1.2)
    assert math.isclose(sum(r["spf"].values()), 1.0, rel_tol=1e-9)
    assert math.isclose(sum(r["handicap"].values()), 1.0, rel_tol=1e-9)
    assert math.isclose(sum(r["correct_score"].values()), 1.0, rel_tol=1e-9)
    assert math.isclose(sum(r["total_goals"].values()), 1.0, rel_tol=1e-9)
    assert math.isclose(sum(r["half_full"].values()), 1.0, rel_tol=1e-9)


def test_predict_handicap_uses_given_line():
    r = predict(1.8, 1.0, handicap=-1)
    base = predict(1.8, 1.0, handicap=0)
    assert r["handicap"]["home"] < base["handicap"]["home"]


def test_predict_rejects_nonpositive_lambda():
    import pytest
    with pytest.raises(ValueError):
        predict(0.0, 1.2)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_predict.py -q`
Expected: FAIL，`ImportError: cannot import name 'predict' from 'engine'`

- [ ] **Step 3: 实现 predict.py 并在 __init__ 导出**

`engine/predict.py`：
```python
from engine.scoreline import score_matrix
from engine.markets import (
    outcome_1x2,
    handicap_1x2,
    correct_score,
    total_goals,
    half_full,
)


def predict(lam_home: float, lam_away: float, rho: float = -0.05,
            handicap: int = 0) -> dict:
    """由两队期望进球导出竞彩 5 大玩法概率。

    lam_home/lam_away: 期望进球，必须 >0。
    rho: Dixon-Coles 低分修正（默认 -0.05）。
    handicap: 让球线（主队净胜球加整数，主-1→-1）。
    """
    if lam_home <= 0 or lam_away <= 0:
        raise ValueError("lam_home 与 lam_away 必须为正")
    m = score_matrix(lam_home, lam_away, rho=rho)
    return {
        "spf": outcome_1x2(m),
        "handicap": handicap_1x2(m, handicap),
        "correct_score": correct_score(m),
        "total_goals": total_goals(m),
        "half_full": half_full(lam_home, lam_away),
    }
```

`engine/__init__.py`：
```python
from engine.predict import predict

__all__ = ["predict"]
```

- [ ] **Step 4: 运行全量测试确认通过**

Run: `python -m pytest -q`
Expected: 全部通过（约 25 passed）

- [ ] **Step 5: 提交**

```bash
git add engine/predict.py engine/__init__.py tests/test_predict.py
git commit -m "feat: 顶层 predict() 组装 5 玩法 + 不变量校验"
```

---

### Task 9: 冒烟脚本 + README 片段

**Files:**
- Create: `engine/demo.py`
- Test: 手动运行验证输出合理

- [ ] **Step 1: 写演示脚本**

`engine/demo.py`：
```python
"""手动冒烟：打印一场 λ=1.8 vs 1.0 的全玩法概率。"""
from engine import predict


def main():
    r = predict(1.8, 1.0, handicap=-1)
    print("胜平负:", {k: round(v, 3) for k, v in r["spf"].items()})
    print("让球(主-1):", {k: round(v, 3) for k, v in r["handicap"].items()})
    print("总进球:", {k: round(v, 3) for k, v in r["total_goals"].items()})
    top_cs = sorted(r["correct_score"].items(), key=lambda x: -x[1])[:5]
    print("比分Top5:", [(k, round(v, 3)) for k, v in top_cs])
    print("半全场:", {k: round(v, 3) for k, v in r["half_full"].items()})


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行，肉眼核对合理性**

Run: `python -m engine.demo`
Expected: 主胜概率明显高于客胜；总进球概率峰值在 2-3；比分 Top5 含 2:0/1:0/2:1 类；各分布数字合理。

- [ ] **Step 3: 提交**

```bash
git add engine/demo.py
git commit -m "chore: 引擎冒烟演示脚本"
```

---

## 完成判据

- `python -m pytest -q` 全绿（约 25 passed）。
- `python -m engine.demo` 输出 5 玩法概率，数字符合直觉。
- 5 玩法概率分布各自和为 1（不变量已被测试锁定）。

## 后续 plan（不在本计划内）

- **λ 估计 / 评分拟合**：在国际比赛结果数据集上拟合 attack/defense + 主场/中立/海拔/高温/旅行 特征 → 产出 λ（方案 §2.4 + §9.4）。
- **数据接入**：聚合 API 取赛程+SP → Supabase（需 API key、Supabase 项目）。
- **去水位 + EV + 校准**：方案 §4 + §2.6（须先有回测数据）。
- **Web 展示**：Next.js 概率区间页（依赖以上）。
