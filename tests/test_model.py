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
