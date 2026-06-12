import datetime

from ratings.model import Ratings
from ratings.lam import expected_goals
from ratings.data import ensure_dataset, load_matches
from ratings.model import fit
from ratings.metrics import brier_score, log_loss
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


# (赛事名, 开赛日, 结束日) —— 用每场自己的 neutral 标记，不再假设整届中立
TOURNAMENTS = [
    ("World Cup 2014", datetime.date(2014, 6, 12), datetime.date(2014, 7, 13)),
    ("World Cup 2018", datetime.date(2018, 6, 14), datetime.date(2018, 7, 15)),
    ("World Cup 2022", datetime.date(2022, 11, 20), datetime.date(2022, 12, 18)),
    ("Euro 2016", datetime.date(2016, 6, 10), datetime.date(2016, 7, 10)),
    ("Euro 2020", datetime.date(2021, 6, 11), datetime.date(2021, 7, 11)),
    ("Euro 2024", datetime.date(2024, 6, 14), datetime.date(2024, 7, 14)),
    ("Copa America 2016", datetime.date(2016, 6, 3), datetime.date(2016, 6, 26)),
    ("Copa America 2019", datetime.date(2019, 6, 14), datetime.date(2019, 7, 7)),
    ("Copa America 2021", datetime.date(2021, 6, 13), datetime.date(2021, 7, 10)),
    ("Copa America 2024", datetime.date(2024, 6, 20), datetime.date(2024, 7, 14)),
    ("AFCON 2019", datetime.date(2019, 6, 21), datetime.date(2019, 7, 19)),
    ("AFCON 2021", datetime.date(2022, 1, 9), datetime.date(2022, 2, 6)),
    ("AFCON 2023", datetime.date(2024, 1, 13), datetime.date(2024, 2, 11)),
]


def run_tournament(all_matches, name, start, end, train_years=12,
                   use_importance=True):
    train_start = datetime.date(start.year - train_years, 1, 1)
    train = [m for m in all_matches if train_start <= m.date < start]
    test = [m for m in all_matches if start <= m.date <= end]
    ratings = fit(train, half_life_days=730.0, use_importance=use_importance)
    probs, outs = [], []
    for m in test:
        probs.append(predict_1x2(ratings, m.home, m.away, neutral=m.neutral))
        outs.append(outcome_of(m.home_score, m.away_score))
    return probs, outs


def run_all(use_importance=True):
    """池化所有赛事，返回聚合 probs/outs 及逐届明细。"""
    matches = load_matches(ensure_dataset())
    all_probs, all_outs, rows = [], [], []
    for name, start, end in TOURNAMENTS:
        probs, outs = run_tournament(matches, name, start, end,
                                     use_importance=use_importance)
        if not probs:
            continue
        all_probs += probs
        all_outs += outs
        rows.append((name, len(probs), brier_score(probs, outs)))
    return all_probs, all_outs, rows


def main():
    for label, use_imp in [("含友谊赛降权", True), ("不降权(基线)", False)]:
        probs, outs, rows = run_all(use_importance=use_imp)
        print(f"\n=== {label} ===")
        for name, n, b in rows:
            print(f"  {name:20s} {n:3d}场 Brier={b:.4f}")
        print(f"  {'池化聚合':20s} {len(probs):3d}场 "
              f"Brier={brier_score(probs, outs):.4f} "
              f"LogLoss={log_loss(probs, outs):.4f}")


if __name__ == "__main__":
    main()
