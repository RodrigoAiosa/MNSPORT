"""Parser do formato Football.TXT (openfootball, domínio público)."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Iterable, Optional

MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

_HEADER = re.compile(r"^=\s*(?P<name>.+?)\s+(?P<year>\d{4})\s*$")
_ROUND = re.compile(r"^[▪»]\s*(?P<round>.+?)\s*$")
_DATE = re.compile(
    r"^\s*(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+)?(?P<mon>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})(?:\s+(?P<year>\d{4}))?\s*$")
_TIME = re.compile(r"^\s*(?P<time>\d{1,2}:\d{2})\s+(?P<rest>.+)$")
_SCORE = re.compile(r"\s+(?P<ft>\d+-\d+)(?P<tail>(?:\s.*)?)$")
_HT = re.compile(r"\((?P<h>\d+)-(?P<a>\d+)\)\s*$")


@dataclass
class Match:
    competition: str
    season: int
    round: str
    date: Optional[str]
    time: Optional[str]
    home: str
    away: str
    home_goals: Optional[int]
    away_goals: Optional[int]
    ht_home: Optional[int]
    ht_away: Optional[int]
    score_raw: str

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def played(self) -> bool:
        return self.home_goals is not None and self.away_goals is not None


def _parse_match_line(body: str):
    if " v " not in body:
        return None
    home, rest = body.split(" v ", 1)
    home, rest = home.strip(), rest.strip()
    m = _SCORE.search(rest)
    if not m:
        return home, rest, "", None, None, None, None
    away = rest[: m.start()].strip()
    score_raw = (m.group("ft") + m.group("tail")).strip()
    # Placares com prorrogação/pênaltis têm semântica ambígua: não inferimos gols.
    if "pen." in score_raw or "a.e.t." in score_raw:
        return home, away, score_raw, None, None, None, None
    hg, ag = (int(x) for x in m.group("ft").split("-"))
    ht = _HT.search(score_raw)
    hh, ha = (int(ht.group("h")), int(ht.group("a"))) if ht else (None, None)
    return home, away, score_raw, hg, ag, hh, ha


def parse_footballtxt(text: str) -> list[Match]:
    competition, season = "", 0
    current_round = ""
    current_date: Optional[date] = None
    matches: list[Match] = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        h = _HEADER.match(line)
        if h:
            competition, season = h.group("name"), int(h.group("year"))
            continue
        r = _ROUND.match(line)
        if r:
            current_round = r.group("round")
            continue
        d = _DATE.match(line)
        if d:
            mon = MONTHS[d.group("mon")]
            if d.group("year"):
                year = int(d.group("year"))
            else:
                year = current_date.year if current_date else season
                if current_date and mon < current_date.month:
                    year += 1  # virada de ano
            current_date = date(year, mon, int(d.group("day")))
            continue
        body, time = line, None
        t = _TIME.match(line)
        if t:
            time, body = t.group("time"), t.group("rest")
        parsed = _parse_match_line(body)
        if not parsed:
            continue
        home, away, raw, hg, ag, hh, ha = parsed
        matches.append(Match(
            competition, season, current_round,
            current_date.isoformat() if current_date else None,
            time, home, away, hg, ag, hh, ha, raw))
    return matches


def standings(matches: Iterable[Match]) -> list[dict]:
    """Classificação por pontos corridos (3/1/0). Só considera jogos com placar."""
    table: dict[str, dict] = {}

    def row(team):
        return table.setdefault(team, dict(team=team, pj=0, v=0, e=0, d=0, gp=0, gc=0))

    for m in matches:
        if not m.played:
            continue
        for team, gf, ga in ((m.home, m.home_goals, m.away_goals), (m.away, m.away_goals, m.home_goals)):
            r = row(team)
            r["pj"] += 1
            r["gp"] += gf
            r["gc"] += ga
            r["v" if gf > ga else "d" if gf < ga else "e"] += 1
    out = []
    for r in table.values():
        r["pts"] = 3 * r["v"] + r["e"]
        r["sg"] = r["gp"] - r["gc"]
        out.append(r)
    out.sort(key=lambda r: (-r["pts"], -r["v"], -r["sg"], -r["gp"], r["team"]))
    for i, r in enumerate(out, 1):
        r["pos"] = i
    return out
