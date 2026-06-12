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
            hs, as_ = _parse_score(row["home_score"]), _parse_score(row["away_score"])
            if hs is None or as_ is None:
                continue
            matches.append(
                Match(
                    date=datetime.date.fromisoformat(row["date"]),
                    home=row["home_team"],
                    away=row["away_team"],
                    home_score=hs,
                    away_score=as_,
                    neutral=row["neutral"].strip().lower() == "true",
                )
            )
    return matches


def _parse_score(value: str):
    """解析比分；缺失（空 / 'NA'）返回 None。"""
    value = value.strip()
    if not value or value.upper() == "NA":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def filter_before(matches: list[Match], cutoff: datetime.date) -> list[Match]:
    return [m for m in matches if m.date < cutoff]
