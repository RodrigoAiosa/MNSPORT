"""Probabilidade de título por simulação (Monte Carlo).

Modelo simples e transparente:
- força de ataque/defesa de cada time = gols marcados/sofridos por jogo na temporada,
  em relação à média da liga (com "encolhimento" para a média, para times com poucos jogos);
- gols de cada jogo restante sorteados por Poisson, com a média da liga para mandante e visitante;
- a tabela final é montada com o mesmo critério da classificação (pontos, vitórias, saldo, gols pró).

É uma estimativa estatística, não uma previsão: não considera elenco, lesões, mando de campo
específico, calendário nem o resultado dos jogos que a fonte ainda não registrou.
"""
from __future__ import annotations

import math
import random
from datetime import date
from typing import Optional

SHRINK_GAMES = 8  # peso (em jogos) da média da liga na força de cada time


def _poisson(rng: random.Random, mu: float) -> int:
    limit, k, p = math.exp(-mu), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def title_probabilities(matches, sims: int = 4000, seed: int = 2026, today: Optional[date] = None):
    """Retorna ({time: probabilidade}, data_do_último_resultado) ou (None, None).

    Só simula temporadas em andamento (a data do último jogo previsto ainda não passou)
    e com pelo menos um jogo ainda sem placar.
    """
    matches = list(matches)
    played = [m for m in matches if m.played]
    todo = [m for m in matches if not m.played and not m.score_raw]
    dates = [m.date for m in matches if m.date]
    today = today or date.today()
    if not played or not todo or not dates or max(dates) < today.isoformat():
        return None, None

    teams = sorted({t for m in matches for t in (m.home, m.away)})
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)

    pts, wins, gd, gf, ga, gp = ([0] * n for _ in range(6))
    home_goals = away_goals = 0
    for m in played:
        h, a = idx[m.home], idx[m.away]
        home_goals += m.home_goals
        away_goals += m.away_goals
        gf[h] += m.home_goals; ga[h] += m.away_goals; gp[h] += 1
        gf[a] += m.away_goals; ga[a] += m.home_goals; gp[a] += 1
        if m.home_goals > m.away_goals:
            pts[h] += 3; wins[h] += 1
        elif m.home_goals < m.away_goals:
            pts[a] += 3; wins[a] += 1
        else:
            pts[h] += 1; pts[a] += 1
    avg_h, avg_a = home_goals / len(played), away_goals / len(played)
    g = (avg_h + avg_a) / 2
    for i in range(n):
        gd[i] = gf[i] - ga[i]
    att = [(gf[i] + SHRINK_GAMES * g) / (gp[i] + SHRINK_GAMES) / g for i in range(n)]
    dfn = [(ga[i] + SHRINK_GAMES * g) / (gp[i] + SHRINK_GAMES) / g for i in range(n)]

    fixtures = []
    for m in todo:
        h, a = idx[m.home], idx[m.away]
        fixtures.append((h, a, max(0.15, avg_h * att[h] * dfn[a]), max(0.15, avg_a * att[a] * dfn[h])))

    rng = random.Random(seed)
    champs = [0] * n
    for _ in range(sims):
        p, w, d, f = pts[:], wins[:], gd[:], gf[:]
        for h, a, mu_h, mu_a in fixtures:
            x, y = _poisson(rng, mu_h), _poisson(rng, mu_a)
            d[h] += x - y; d[a] += y - x; f[h] += x; f[a] += y
            if x > y:
                p[h] += 3; w[h] += 1
            elif x < y:
                p[a] += 3; w[a] += 1
            else:
                p[h] += 1; p[a] += 1
        best = max(range(n), key=lambda i: (p[i], w[i], d[i], f[i], rng.random()))
        champs[best] += 1

    return {t: champs[idx[t]] / sims for t in teams}, max(m.date for m in played if m.date)
