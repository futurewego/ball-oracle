import math
from pipeline.devig import multiplicative, shin, rtp, booksum


SPF = [1.50, 4.00, 6.00]  # 强主队样例(主胜/平/客胜)


def test_multiplicative_sums_to_one():
    assert math.isclose(sum(multiplicative(SPF)), 1.0, rel_tol=1e-9)


def test_shin_sums_to_one():
    assert math.isclose(sum(shin(SPF)), 1.0, rel_tol=1e-9)


def test_rtp_below_one_for_overround_book():
    assert rtp(SPF) < 1.0
    assert booksum(SPF) > 1.0


def test_devig_lowers_probabilities_vs_raw():
    # 去水位=除以水位和(>1),剥离水位后概率应 < 原始 1/SP
    p = multiplicative(SPF)
    assert p[0] < 1.0 / SPF[0]


def test_shin_close_to_multiplicative_for_small_overround():
    fair = [2.04, 2.04]  # 接近无水位的两选项
    s, m = shin(fair), multiplicative(fair)
    assert math.isclose(s[0], m[0], abs_tol=0.02)
