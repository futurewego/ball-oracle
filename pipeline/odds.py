"""SP 赔率数据源适配器（方案 §5.1 / §8-P0）。

竞彩 poolCode ↔ 玩法（已核实精确对应）：
  had=胜平负  hhad=让球胜平负  ttg=总进球  hafu=半全场  crs=比分
官方接口（无开放 API；须中国 IP + 浏览器头；本境外环境会被反爬拦）：
  https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry
    ?poolCode=had,hhad,ttg,hafu,crs&channel=c
"""
POOL_CODES = {"had": "胜平负", "hhad": "让球胜平负",
              "ttg": "总进球", "hafu": "半全场", "crs": "比分"}
SPORTTERY_ENDPOINT = (
    "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry"
    "?poolCode=had,hhad,ttg,hafu,crs&channel=c"
)


class OddsSource:
    """赔率源接口：fetch() 返回 {matchKey: {market: {outcome: sp}}}。"""
    def fetch(self) -> dict:
        raise NotImplementedError


class ManualSource(OddsSource):
    """手动/样例源（可测）：直接传入赔率字典。"""
    def __init__(self, data: dict):
        self._data = data

    def fetch(self) -> dict:
        return self._data


class SportterySource(OddsSource):
    """竞彩官方源。⚠️ 未在本环境验证（境外被反爬）；须在中国侧运行。
    解析需对照真实 JSON 结构对齐（拿到样例后补 _parse）。"""
    def fetch(self) -> dict:
        import json
        import urllib.request
        req = urllib.request.Request(SPORTTERY_ENDPOINT, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.sporttery.cn/",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = json.loads(r.read().decode("utf-8"))
        return self._parse(raw)

    def _parse(self, raw: dict) -> dict:
        # TODO: 拿到真实 JSON 样例后按 poolCode 映射到 {market:{outcome:sp}}
        raise NotImplementedError("需对照真实 sporttery JSON 结构实现解析")
