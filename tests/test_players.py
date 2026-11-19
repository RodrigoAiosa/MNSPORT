import pytest

from mnsport.players import PlayersError, find_team, parse_players, team_players

TEAMS = {"errors": [], "response": [
    {"team": {"id": 127, "name": "Flamengo"}}, {"team": {"id": 121, "name": "Palmeiras"}},
    {"team": {"id": 119, "name": "Internacional"}}, {"team": {"id": 1062, "name": "Atletico-MG"}},
    {"team": {"id": 134, "name": "Athletico-PR"}}, {"team": {"id": 130, "name": "Gremio"}}]}


def player(pid, name, minutes, goals, rating="7.10", league=71):
    return {"player": {"id": pid, "name": name, "age": 28, "nationality": "Brazil"},
            "statistics": [{"league": {"id": league}, "games": {"appearences": 10, "minutes": minutes, "position": "Attacker", "rating": rating},
                            "goals": {"total": goals, "assists": None}, "cards": {"yellow": 2, "red": 0}}]}


def test_find_team_handles_openfootball_names():
    assert find_team(TEAMS, "CR Flamengo")["id"] == 127
    assert find_team(TEAMS, "CA Mineiro")["id"] == 1062
    assert find_team(TEAMS, "CA Paranaense")["id"] == 134
    assert find_team(TEAMS, "Grêmio FBPA")["id"] == 130
    with pytest.raises(PlayersError):
        find_team(TEAMS, "Time Inexistente")


def test_parse_players_sorts_and_defaults():
    rows = parse_players([{"response": [player(1, "A", 300, None), player(2, "B", 900, 7), player(3, "C", 100, 1, league=999)]}], 71)
    assert [r["name"] for r in rows] == ["B", "A"]  # C é de outra liga
    assert rows[0]["goals"] == 7 and rows[1]["goals"] == 0 and rows[0]["assists"] == 0 and rows[0]["rating"] == 7.1


def test_team_players_paginates_and_reports_errors():
    calls = []

    def fake(path, key):
        calls.append(path)
        if path.startswith("/teams"):
            return TEAMS
        n = int(path.rsplit("page=", 1)[1])
        return {"errors": [], "paging": {"total": 2}, "response": [player(n, f"P{n}", 100 * n, n)]}

    out = team_players("CR Flamengo", 2025, "br1", key="k", call=fake)
    assert out["team"] == "Flamengo" and [p["name"] for p in out["players"]] == ["P2", "P1"]
    assert len(calls) == 3

    def blocked(path, key):
        return {"errors": {"plan": "Free plans do not have access to this season, try from 2021 to 2023."}, "response": []}

    with pytest.raises(PlayersError) as e:
        team_players("CR Flamengo", 2026, "br1", key="k", call=blocked)
    assert e.value.code == "plan" and "2021 to 2023" in str(e.value)


def test_team_players_requires_key(monkeypatch):
    monkeypatch.delenv("APIFOOTBALL_KEY", raising=False)
    with pytest.raises(PlayersError) as e:
        team_players("Flamengo", 2025)
    assert e.value.code == "no_key"
