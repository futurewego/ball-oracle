from ratings.adjust import apply_conditions


def test_defaults_are_noop():
    lh, la = apply_conditions(1.5, 1.2)
    assert (lh, la) == (1.5, 1.2)


def test_high_altitude_penalizes_sea_level_team_more():
    # 海平面队(home_alt=0) vs 高原队(away_alt=2200) 在 2240m 赛地
    lh, la = apply_conditions(1.5, 1.5, elevation_m=2240,
                              home_altitude_m=0, away_altitude_m=2200)
    assert lh < 1.5          # 海平面主队被折扣
    assert la > lh           # 高原客队几乎不受影响，相对更高


def test_heat_reduces_both_sides():
    lh, la = apply_conditions(1.5, 1.2, temp_c=40)
    assert lh < 1.5 and la < 1.2


def test_no_heat_below_threshold():
    lh, la = apply_conditions(1.5, 1.2, temp_c=20)
    assert (lh, la) == (1.5, 1.2)


def test_less_rest_penalizes_that_team_only():
    lh, la = apply_conditions(1.5, 1.5, home_rest_days=2, away_rest_days=4)
    assert lh < 1.5      # 主队休息少被折扣
    assert la == 1.5     # 客队休息充足不变
