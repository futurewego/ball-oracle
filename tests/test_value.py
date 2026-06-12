import math
from pipeline.value import ev, evaluate_market

MODEL = {"home": 0.55, "draw": 0.24, "away": 0.21}
SPS = {"home": 1.50, "draw": 4.00, "away": 6.00}


def test_ev_formula():
    assert math.isclose(ev(0.5, 2.5), 0.25, rel_tol=1e-9)


def test_market_probs_sum_to_one():
    r = evaluate_market(MODEL, SPS)
    assert math.isclose(sum(v["market_p"] for v in r.values()), 1.0, abs_tol=1e-3)


def test_no_value_flag_when_unvalidated():
    # 诚实闸门：未验证时,即便EV为正也不标记价值
    r = evaluate_market(MODEL, SPS, validated=False)
    assert all(v["is_value"] is False for v in r.values())


def test_value_flag_requires_validation_and_positive_ev():
    r = evaluate_market(MODEL, SPS, validated=True, ev_threshold=0.05)
    # home: 0.55*1.5-1 = -0.175 <0 -> 非价值; 需要EV>阈值才标记
    assert r["home"]["is_value"] is False
    # 构造一个正EV高于阈值的选项
    r2 = evaluate_market({"x": 0.5, "y": 0.5}, {"x": 2.5, "y": 1.7},
                         validated=True, ev_threshold=0.05)
    assert r2["x"]["ev"] > 0.05 and r2["x"]["is_value"] is True


def test_keys_preserved():
    r = evaluate_market(MODEL, SPS)
    assert set(r.keys()) == {"home", "draw", "away"}
