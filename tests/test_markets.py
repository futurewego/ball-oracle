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
