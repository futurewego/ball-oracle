"""2026 世界杯小组赛完整赛程（12组×6场=72场循环赛）。

分组数据源：Al Jazeera 2026 世界杯完整赛程（已与评分库逐队核对，48 队全对齐）。
东道主美/加/墨主场 neutral=False；其余中立场。每组循环赛固定 3 轮配对。
轮次日期为代表性日期（小组赛 2026-06-11~27），UI 以"组+轮次"展示。
"""
import datetime
from dataclasses import dataclass

# 12 组抽签（英文队名须与 martj42 评分库一致）
GROUPS: dict[str, list[str]] = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

CN: dict[str, str] = {
    "Mexico": "墨西哥", "South Africa": "南非", "South Korea": "韩国", "Czech Republic": "捷克",
    "Canada": "加拿大", "Bosnia and Herzegovina": "波黑", "Qatar": "卡塔尔", "Switzerland": "瑞士",
    "Brazil": "巴西", "Morocco": "摩洛哥", "Haiti": "海地", "Scotland": "苏格兰",
    "United States": "美国", "Paraguay": "巴拉圭", "Australia": "澳大利亚", "Turkey": "土耳其",
    "Germany": "德国", "Curaçao": "库拉索", "Ivory Coast": "科特迪瓦", "Ecuador": "厄瓜多尔",
    "Netherlands": "荷兰", "Japan": "日本", "Sweden": "瑞典", "Tunisia": "突尼斯",
    "Belgium": "比利时", "Egypt": "埃及", "Iran": "伊朗", "New Zealand": "新西兰",
    "Spain": "西班牙", "Cape Verde": "佛得角", "Saudi Arabia": "沙特", "Uruguay": "乌拉圭",
    "France": "法国", "Senegal": "塞内加尔", "Iraq": "伊拉克", "Norway": "挪威",
    "Argentina": "阿根廷", "Algeria": "阿尔及利亚", "Austria": "奥地利", "Jordan": "约旦",
    "Portugal": "葡萄牙", "DR Congo": "刚果(金)", "Uzbekistan": "乌兹别克", "Colombia": "哥伦比亚",
    "England": "英格兰", "Croatia": "克罗地亚", "Ghana": "加纳", "Panama": "巴拿马",
}

HOSTS = {"Mexico", "United States", "Canada"}

# 每组循环赛配对(队索引)与轮次
_PAIRINGS = [((0, 1), 1), ((2, 3), 1), ((0, 2), 2), ((1, 3), 2), ((0, 3), 3), ((1, 2), 3)]
_MATCHDAY_DATE = {1: "2026-06-14", 2: "2026-06-20", 3: "2026-06-26"}

TOURNAMENT_START = datetime.date(2026, 6, 11)


@dataclass(frozen=True)
class Fixture:
    date: datetime.date
    group: str
    matchday: int
    home: str
    away: str
    neutral: bool
    cn: str


def load_fixtures() -> list[Fixture]:
    out: list[Fixture] = []
    for g, teams in GROUPS.items():
        for (i, j), md in _PAIRINGS:
            a, b = teams[i], teams[j]
            if a in HOSTS or b in HOSTS:
                home, away = (a, b) if a in HOSTS else (b, a)
                neutral = False
            else:
                home, away = a, b
                neutral = True
            out.append(Fixture(
                date=datetime.date.fromisoformat(_MATCHDAY_DATE[md]),
                group=g, matchday=md, home=home, away=away, neutral=neutral,
                cn=f"{CN[home]} vs {CN[away]}",
            ))
    return out
