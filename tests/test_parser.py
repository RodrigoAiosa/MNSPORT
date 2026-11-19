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


# ---- probabilidade de título ----
from datetime import date
from mnsport.forecast import title_probabilities
from mnsport.parser import Match


def _m(home, away, hg=None, ag=None, d="2030-05-01"):
    return Match("Liga", 2030, "R", d, None, home, away, hg, ag, None, None, "" if hg is None else f"{hg}-{ag}")


def test_forecast_sums_to_one_and_favors_leader():
    ms = [_m("A", "B", 3, 0, "2030-01-01"), _m("C", "D", 1, 0, "2030-01-01"),
          _m("B", "C", 0, 0, "2030-02-01"), _m("A", "D", 2, 0, "2030-02-01"),
          _m("A", "C", d="2030-05-01"), _m("B", "D", d="2030-05-01")]
    probs, as_of = title_probabilities(ms, today=date(2030, 3, 1))
    assert abs(sum(probs.values()) - 1) < 1e-9
    assert probs["A"] > 0.6 and probs["D"] < probs["A"]
    assert as_of == "2030-02-01"


def test_forecast_is_certain_when_decided():
    ms = [_m("A", "B", 5, 0, "2030-01-01"), _m("A", "B", d="2030-05-01")]
    # A tem 3 pts + jogo restante; B só pode empatar em pontos e perde em saldo
    probs, _ = title_probabilities(ms, today=date(2030, 3, 1))
    assert probs["A"] > 0.99


def test_forecast_skipped_when_season_over_or_nothing_left():
    done = [_m("A", "B", 1, 0, "2030-01-01")]
    assert title_probabilities(done, today=date(2030, 3, 1)) == (None, None)
    gap = [_m("A", "B", 1, 0, "2030-01-01"), _m("B", "A", d="2030-02-01")]  # fonte incompleta: temporada já acabou
    assert title_probabilities(gap, today=date(2030, 6, 1)) == (None, None)
