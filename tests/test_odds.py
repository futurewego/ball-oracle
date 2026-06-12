from pipeline.odds import parse, ManualSource

RAW = {"value": {"matchInfoList": [{"businessDate": "2026-06-12", "subMatchList": [
    {"homeTeamAllName": "加拿大", "awayTeamAllName": "波黑",
     "matchDate": "2026-06-13", "matchNumStr": "周五003",
     "had": {"h": "1.61", "d": "3.36", "a": "4.75"},
     "hhad": {"h": "3.32", "d": "3.07", "a": "1.99", "goalLineValue": "-1.00"},
     "ttg": {"s0": "9.50", "s1": "4.30", "s2": "3.00", "s3": "3.60",
             "s4": "6.20", "s5": "13.00", "s6": "24.00", "s7": "40.00"},
     "hafu": {"hh": "2.53", "hd": "15.5", "ha": "36.0", "dh": "4.25", "dd": "4.80",
              "da": "10.0", "ah": "25.0", "ad": "15.5", "aa": "8.40"},
     "crs": {"s01s00": "5.40", "s00s00": "9.50", "s00s00f": "0"}},
]}]}}


def test_parse_one_match():
    ms = parse(RAW)
    assert len(ms) == 1
    assert ms[0]["home_cn"] == "加拿大" and ms[0]["away_cn"] == "波黑"


def test_parse_had():
    m = parse(RAW)[0]
    assert m["had"] == {"home": 1.61, "draw": 3.36, "away": 4.75}


def test_parse_ttg_eight_buckets():
    m = parse(RAW)[0]
    assert set(m["ttg"].keys()) == {"0", "1", "2", "3", "4", "5", "6", "7+"}


def test_parse_hafu_nine():
    assert len(parse(RAW)[0]["hafu"]) == 9


def test_parse_crs_and_skips_f_keys():
    crs = parse(RAW)[0]["crs"]
    assert crs["1:0"] == 5.40 and crs["0:0"] == 9.50
    assert all("f" not in k for k in crs)  # *f 键被跳过


def test_manual_source():
    assert len(ManualSource(RAW).fetch()) == 1
