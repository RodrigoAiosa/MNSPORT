# MNSPORT

Ferramenta em Python (sem dependências externas) para coletar **dados públicos dos times do Brasil**:
jogos, resultados, classificação, lista de clubes e ficha do clube.

## Fontes

| Dado | Fonte | Licença |
|---|---|---|
| Jogos e resultados (Série A, Série B, Copa do Brasil) | [openfootball/south-america](https://github.com/openfootball/south-america) | Domínio público |
| Ficha do clube (estádio, fundação, escudo…) | [TheSportsDB](https://www.thesportsdb.com/) (API gratuita) | Ver termos do TheSportsDB |

## Uso

```bash
pip install -e .            # ou: python -m mnsport ...

mnsport matches   --season 2025 --division br1 --team Flamengo -o flamengo.csv
mnsport standings --season 2025 --division br1 --format json
mnsport teams     --season 2026 --division br1
mnsport team-info "Palmeiras"
```

Divisões: `br1` (Série A), `br2` (Série B), `brcup` (Copa do Brasil). Os arquivos baixados ficam em
cache (`~/.cache/mnsport`, ajustável com `MNSPORT_CACHE`); use `--refresh` para atualizar.
`--file caminho.txt` lê um arquivo Football.TXT local.
Para `team-info`, a chave da API pode ser definida em `THESPORTSDB_KEY` (padrão: chave de teste `123`).

## Probabilidade de título e jogadores

- **Chance de título** (coluna na classificação da Série A/B, só em temporadas em andamento): simulação Monte Carlo
  (4 mil temporadas) dos jogos que faltam, com gols sorteados por Poisson a partir da força de ataque/defesa de cada time
  (`mnsport/forecast.py`). É uma estimativa estatística, não uma previsão.
- **Jogadores** (aba Jogadores): estatísticas por time via [API-Football](https://www.api-football.com/) (`mnsport/players.py`).
  Exige uma chave gratuita na variável de ambiente `APIFOOTBALL_KEY` (na Vercel: Settings › Environment Variables).
  O plano gratuito tem limite diário e pode não cobrir todas as temporadas; as respostas ficam em cache por 12 h para poupar a cota.

## Limitações conhecidas

- A cobertura depende do openfootball: alguns jogos (ex.: boa parte da Série B 2025) estão **sem placar** na fonte.
  Esses jogos saem com gols vazios e ficam fora da classificação.
- Jogos com prorrogação/pênaltis (Copa do Brasil) têm o placar guardado em `score_raw`, sem gols inferidos.
- A classificação usa só pontos corridos (3/1/0; desempate: vitórias, saldo, gols pró); não vale para mata-mata.
- O comando `team-info` depende de acesso à API do TheSportsDB; o código é coberto por teste com resposta simulada.

## Testes

```bash
pip install pytest && pytest
```

## Site (Vercel)

`public/index.html` é o site estático (classificação e jogos) e `api/standings.py` / `api/matches.py`
são funções Python que ele consome (`/api/standings?season=2025&division=br1`).
Basta importar o repositório na Vercel, sem configuração extra.
