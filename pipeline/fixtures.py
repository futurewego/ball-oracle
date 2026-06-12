"""2026 世界杯赛程（真实对阵；东道主美/加/墨主场 neutral=False）。

这是赛程数据源——结构稳定，后续可换成抓取/接口，对阵 (home,away,date,venue,
neutral,group) 即可。队名须与评分库(martj42 数据集)一致。
"""
import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class Fixture:
    date: datetime.date
    home: str
    away: str
    venue: str
    neutral: bool
    group: str
    cn: str  # 中文对阵名（展示用）


def _d(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s)


# 真实 2026 世界杯小组赛首轮部分对阵（数据源：ESPN / Al Jazeera 赛程）
WC2026: list[Fixture] = [
    Fixture(_d("2026-06-11"), "Mexico", "South Africa", "墨西哥城·阿兹特克", False, "A", "墨西哥 vs 南非"),
    Fixture(_d("2026-06-12"), "Canada", "Bosnia and Herzegovina", "多伦多", False, "B", "加拿大 vs 波黑"),
    Fixture(_d("2026-06-12"), "United States", "Paraguay", "洛杉矶·英格尔伍德", False, "D", "美国 vs 巴拉圭"),
    Fixture(_d("2026-06-13"), "Qatar", "Switzerland", "中立场", True, "B", "卡塔尔 vs 瑞士"),
    Fixture(_d("2026-06-13"), "Brazil", "Morocco", "中立场", True, "C", "巴西 vs 摩洛哥"),
    Fixture(_d("2026-06-14"), "Germany", "Curaçao", "中立场", True, "E", "德国 vs 库拉索"),
    Fixture(_d("2026-06-14"), "Netherlands", "Japan", "中立场", True, "F", "荷兰 vs 日本"),
    Fixture(_d("2026-06-15"), "Spain", "Cape Verde", "中立场", True, "H", "西班牙 vs 佛得角"),
]

# 评分拟合的训练截止（赛事开赛日）——用此前全部国际赛果
TOURNAMENT_START = _d("2026-06-11")


def load_fixtures() -> list[Fixture]:
    return list(WC2026)
