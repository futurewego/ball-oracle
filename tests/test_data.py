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
