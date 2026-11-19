from __future__ import annotations

import argparse
import csv
import json
import sys

from . import sources
from .parser import parse_footballtxt, standings


def _write(rows: list[dict], fmt: str, out: str | None) -> None:
    f = open(out, "w", encoding="utf-8", newline="") if out else sys.stdout
    try:
        if fmt == "json":
            json.dump(rows, f, ensure_ascii=False, indent=2)
            f.write("\n")
        elif rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    finally:
        if out:
            f.close()


def _matches(args):
    text = open(args.file, encoding="utf-8").read() if args.file else sources.fetch_season(
        args.season, args.division, args.refresh)
    ms = parse_footballtxt(text)
    if getattr(args, "team", None):
        t = args.team.lower()
        ms = [m for m in ms if t in m.home.lower() or t in m.away.lower()]
    return ms


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mnsport", description="Dados públicos dos times do Brasil")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--season", type=int, default=2025)
        sp.add_argument("--division", choices=list(sources.DIVISIONS), default="br1")
        sp.add_argument("--file", help="arquivo Football.TXT local (em vez de baixar)")
        sp.add_argument("--refresh", action="store_true", help="ignora o cache")
        sp.add_argument("--format", choices=["csv", "json"], default="csv")
        sp.add_argument("-o", "--output")

    s = sub.add_parser("matches", help="jogos e resultados"); common(s); s.add_argument("--team")
    s = sub.add_parser("standings", help="classificação (pontos corridos)"); common(s)
    s = sub.add_parser("teams", help="lista de times da competição"); common(s)
    s = sub.add_parser("team-info", help="ficha do clube (TheSportsDB)")
    s.add_argument("name"); s.add_argument("--format", choices=["csv", "json"], default="json"); s.add_argument("-o", "--output")

    a = p.parse_args(argv)
    if a.cmd == "matches":
        rows = [m.as_dict() for m in _matches(a)]
    elif a.cmd == "standings":
        rows = standings(_matches(a))
    elif a.cmd == "teams":
        rows = [{"team": t} for t in sorted({x for m in _matches(a) for x in (m.home, m.away)})]
    else:
        rows = sources.team_info(a.name)
    _write(rows, a.format, a.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
