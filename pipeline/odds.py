"""SP 赔率数据源适配器（方案 §5.1）。已对接真实 sporttery 接口。

竞彩 poolCode ↔ 玩法：had=胜平负 hhad=让球 ttg=总进球 hafu=半全场 crs=比分
接口须带 Referer/Origin 头(否则被 anti-bot 拦)。
"""
import json
import re
import urllib.request

SPORTTERY_ENDPOINT = (
    "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry"
    "?poolCode=had,hhad,ttg,hafu,crs&channel=c"
)
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Referer": "https://www.sporttery.cn/jc/zqdg/",
    "Origin": "https://www.sporttery.cn",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

_TTG_KEYS = {"s0": "0", "s1": "1", "s2": "2", "s3": "3",
             "s4": "4", "s5": "5", "s6": "6", "s7": "7+"}
_HAFU_KEYS = {"hh": "胜胜", "hd": "胜平", "ha": "胜负", "dh": "平胜", "dd": "平平",
              "da": "平负", "ah": "负胜", "ad": "负平", "aa": "负负"}


def _f(x):
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def _odds_group(d, keymap):
    out = {}
    for src, dst in keymap.items():
        v = _f(d.get(src))
        if v is not None:
            out[dst] = v
    return out


def parse(raw: dict) -> list[dict]:
    """sporttery JSON → 每场 {home_cn,away_cn,date,had,hhad,ttg,hafu,crs}。"""
    matches = []
    for day in raw["value"]["matchInfoList"]:
        for sm in day["subMatchList"]:
            had = sm.get("had", {})
            hhad = sm.get("hhad", {})
            rec = {
                "home_cn": sm.get("homeTeamAllName"),
                "away_cn": sm.get("awayTeamAllName"),
                "date": sm.get("matchDate"),
                "num": sm.get("matchNumStr"),
                "had": _odds_group(had, {"h": "home", "d": "draw", "a": "away"}),
                "hhad": _odds_group(hhad, {"h": "home", "d": "draw", "a": "away"}),
                "hhad_line": hhad.get("goalLineValue") or hhad.get("goalLine"),
                "ttg": _odds_group(sm.get("ttg", {}), _TTG_KEYS),
                "hafu": _odds_group(sm.get("hafu", {}), _HAFU_KEYS),
            }
            # 比分 crs: sHHsAA -> "H:A"
            crs = {}
            for k, v in sm.get("crs", {}).items():
                mobj = re.match(r"^s(\d{1,2})s(\d{1,2})$", k)  # 跳过 *f 及"其它"键
                if mobj:
                    f = _f(v)
                    if f is not None:
                        crs[f"{int(mobj.group(1))}:{int(mobj.group(2))}"] = f
            rec["crs"] = crs
            matches.append(rec)
    return matches


class OddsSource:
    def fetch(self) -> list[dict]:
        raise NotImplementedError


class ManualSource(OddsSource):
    def __init__(self, raw):
        self._raw = raw

    def fetch(self):
        return parse(self._raw)


class SportterySource(OddsSource):
    """竞彩官方实时源。须带浏览器头；从可直连 sporttery 的网络运行。"""
    def fetch(self):
        req = urllib.request.Request(SPORTTERY_ENDPOINT, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = json.loads(r.read().decode("utf-8"))
        return parse(raw)
