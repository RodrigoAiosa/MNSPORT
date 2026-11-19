import json

from mnsport.parser import parse_footballtxt, standings
from mnsport import sources

SAMPLE = """= Brasileiro Série A 2025

# Date       Sat Mar 29 - Sun Dec 7 2025 (253d)

▪ Matchday 1
  Sat Mar 29 2025
    18:30  São Paulo FC            v SC Recife                0-0
           Cruzeiro EC             v Mirassol FC              2-1 (2-1)
  Sun Mar 30
    16:00  SE Palmeiras            v Botafogo FR
▪ Matchday 38
  Sun Dec 7
    16:00  Botafogo FR             v Cruzeiro EC              0-3 (0-1)
  Mon Jan 5
    16:00  São Paulo FC            v Mirassol FC              1-0
▪ Round 1
  Tue Feb 18 2025
    18:00  Tocantinópolis TO       v Atlético Mineiro         1-4 pen. 1-4 a.e.t. (1-1, 0-0)
"""


def test_parse_basic():
    ms = parse_footballtxt(SAMPLE)
    assert len(ms) == 6
    m = ms[1]
    assert (m.home, m.away, m.home_goals, m.away_goals, m.ht_home, m.ht_away) == ("Cruzeiro EC", "Mirassol FC", 2, 1, 2, 1)
    assert m.date == "2025-03-29" and m.round == "Matchday 1" and m.competition == "Brasileiro Série A"
    assert ms[0].time == "18:30" and ms[0].ht_home is None


def test_unplayed_and_year_rollover_and_penalties():
    ms = parse_footballtxt(SAMPLE)
    assert not ms[2].played and ms[2].away == "Botafogo FR"
    assert ms[4].date == "2026-01-05"
    assert ms[5].home_goals is None and "pen." in ms[5].score_raw


def test_standings():
    t = standings(parse_footballtxt(SAMPLE))
    cru = next(r for r in t if r["team"] == "Cruzeiro EC")
    assert (cru["pts"], cru["sg"], cru["pj"]) == (6, 4, 2)
    assert t[0]["team"] == "Cruzeiro EC" and t[0]["pos"] == 1


def test_team_info_filters_brazil():
    payload = json.dumps({"teams": [
        {"strTeam": "Flamengo", "strCountry": "Brazil", "strStadium": "Maracanã"},
        {"strTeam": "Flamengo FC", "strCountry": "Other"}]}).encode()
    r = sources.team_info("Flamengo", fetch=lambda url: payload)
    assert [x["strTeam"] for x in r] == ["Flamengo"]
