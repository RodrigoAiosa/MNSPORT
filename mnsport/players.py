"""Estatísticas de jogadores por time via API-Football (api-sports.io).

Requer uma chave gratuita (https://dashboard.api-football.com/register) na variável de
ambiente APIFOOTBALL_KEY. O plano gratuito tem limite diário de consultas e pode não cobrir
todas as temporadas; essas mensagens da API são repassadas ao usuário.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import unicodedata
import urllib.request

BASE = "https://v3.football.api-sports.io"
LEAGUES = {"br1": 71, "br2": 72}  # Série A, Série B
MAX_PAGES = 3  # limite do plano gratuito (20 jogadores por página) e trava contra estourar a cota diária


class PlayersError(Exception):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message)
        self.code = code


def _call(path: str, key: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(BASE + path, headers={"x-apisports-key": key, "User-Agent": "mnsport/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _check(payload: dict) -> dict:
    errors = payload.get("errors")
    if errors:  # a API devolve [] quando está tudo certo e {campo: mensagem} quando não
        text = "; ".join(errors.values()) if isinstance(errors, dict) else str(errors)
        low = text.lower()
        code = "plan" if "plan" in low else "limit" if "limit" in low or "request" in low else "error"
        raise PlayersError(text, code)
    return payload


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()


_AFFIX = {"cr", "se", "sc", "ec", "ca", "rb", "fc", "fr", "fbc", "af", "fbpa", "ac"}
_ALIAS = {"ca mineiro": "atletico mg", "ca paranaense": "athletico pr", "sc recife": "sport recife",
          "sc corinthians paulista": "corinthians", "cr vasco da gama": "vasco", "gremio fbpa": "gremio"}


def _variants(name: str) -> list[str]:
    n = _norm(name)
    parts = n.split()
    while len(parts) > 1 and parts[0] in _AFFIX:
        parts.pop(0)
    while len(parts) > 1 and parts[-1] in _AFFIX:
        parts.pop()
    out = [n, " ".join(parts)]
    if n in _ALIAS:
        out.append(_ALIAS[n])
    return out


def find_team(teams_payload: dict, name: str) -> dict:
    """Escolhe, entre os times da API, o que melhor corresponde ao nome do openfootball."""
    mine = _variants(name)
    best, score = None, 0.0
    for item in teams_payload.get("response", []):
        theirs = _variants(item["team"]["name"])
        s = max(difflib.SequenceMatcher(None, a, b).ratio() + (0.2 if a in b or b in a else 0)
                for a in mine for b in theirs)
        if s > score:
            best, score = item["team"], s
    if not best or score < 0.75:
        raise PlayersError(f"Não encontrei “{name}” na fonte de jogadores.", "team_not_found")
    return best


def parse_players(pages: list[dict], league: int) -> list[dict]:
    rows = []
    for page in pages:
        for item in page.get("response", []):
            p = item["player"]
            st = [s for s in item.get("statistics", []) if (s.get("league") or {}).get("id") in (league, None)]
            if not st:
                continue
            s = st[0]
            g = s.get("games") or {}
            rating = g.get("rating")
            rows.append({
                "id": p["id"], "name": p["name"], "age": p.get("age"), "nationality": p.get("nationality"),
                "photo": p.get("photo"),
                "position": g.get("position"),
                "apps": g.get("appearences", g.get("appearances")) or 0,
                "minutes": g.get("minutes") or 0,
                "goals": (s.get("goals") or {}).get("total") or 0,
                "assists": (s.get("goals") or {}).get("assists") or 0,
                "yellow": (s.get("cards") or {}).get("yellow") or 0,
                "red": (s.get("cards") or {}).get("red") or 0,
                "rating": round(float(rating), 2) if rating else None,
            })
    rows.sort(key=lambda r: (-r["minutes"], r["name"]))
    return rows


def team_players(team_name: str, season: int, division: str = "br1", key: str | None = None, call=_call) -> dict:
    key = key or os.environ.get("APIFOOTBALL_KEY")
    if not key:
        raise PlayersError("A chave da API-Football não está configurada.", "no_key")
    if division not in LEAGUES:
        raise PlayersError("Estatísticas de jogadores só estão disponíveis para as Séries A e B.", "division")
    league = LEAGUES[division]
    team = find_team(_check(call(f"/teams?league={league}&season={season}", key)), team_name)
    pages, page, total = [], 1, 1
    while page <= total and page <= MAX_PAGES:
        payload = _check(call(f"/players?team={team['id']}&league={league}&season={season}&page={page}", key))
        pages.append(payload)
        total = (payload.get("paging") or {}).get("total", 1) or 1
        page += 1
    return {"team": team["name"], "season": season, "players": parse_players(pages, league)}
