"""Fontes públicas de dados.

- openfootball/south-america (GitHub, domínio público): jogos e resultados
  do Brasileirão (Série A/B) e Copa do Brasil.
- TheSportsDB (API pública gratuita): ficha do clube (estádio, fundação, escudo...).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

OPENFOOTBALL_RAW = "https://raw.githubusercontent.com/openfootball/south-america/master/brazil/{season}_{division}.txt"
THESPORTSDB = "https://www.thesportsdb.com/api/v1/json/{key}/searchteams.php?t={name}"
DIVISIONS = {"br1": "Série A", "br2": "Série B", "brcup": "Copa do Brasil"}
CACHE_DIR = Path(os.environ.get("MNSPORT_CACHE", Path.home() / ".cache" / "mnsport"))


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "mnsport/0.1 (+https://github.com/RodrigoAiosa/MNSPORT)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_season(season: int, division: str = "br1", refresh: bool = False) -> str:
    if division not in DIVISIONS:
        raise ValueError(f"divisão inválida: {division} (use {', '.join(DIVISIONS)})")
    cache = CACHE_DIR / f"{season}_{division}.txt"
    if cache.exists() and not refresh:
        return cache.read_text(encoding="utf-8")
    text = _get(OPENFOOTBALL_RAW.format(season=season, division=division)).decode("utf-8")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return text


def team_info(name: str, fetch=_get) -> list[dict]:
    """Ficha de clube via TheSportsDB. `fetch` é injetável para testes."""
    key = os.environ.get("THESPORTSDB_KEY", "123")
    url = THESPORTSDB.format(key=key, name=urllib.parse.quote(name))
    data = json.loads(fetch(url))
    wanted = ("idTeam", "strTeam", "strAlternate", "strLeague", "intFormedYear",
              "strStadium", "intStadiumCapacity", "strLocation", "strCountry",
              "strWebsite", "strBadge")
    return [{k: t.get(k) for k in wanted} for t in (data.get("teams") or [])
            if (t.get("strCountry") or "").lower() == "brazil"]
