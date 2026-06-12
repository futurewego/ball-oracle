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
