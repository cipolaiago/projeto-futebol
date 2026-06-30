# Guia da football-data.org API

Este projeto comeca pela API v4 da football-data.org.

## Token
Use uma variavel de ambiente:

```powershell
$env:FOOTBALL_DATA_TOKEN = "seu_token_aqui"
```

Todas as chamadas autenticadas usam o header:

```text
X-Auth-Token: <token>
```
## Base da API

```text
https://api.football-data.org/v4
```

Exemplo minimo com `curl`:

```bash
curl "https://api.football-data.org/v4/competitions" \
  -H "X-Auth-Token: $FOOTBALL_DATA_TOKEN"
```

Exemplo minimo em Python, sem dependencia externa:

```python
import json
import os
import urllib.request

BASE_URL = "https://api.football-data.org/v4"
TOKEN = os.environ["FOOTBALL_DATA_TOKEN"]


def get_json(path: str, params: str = "") -> dict:
    url = f"{BASE_URL}{path}{params}"
    request = urllib.request.Request(url, headers={"X-Auth-Token": TOKEN})
    with urllib.request.urlopen(request) as response:
        print("requests_left:", response.headers.get("X-RequestsAvailable"))
        print("reset_seconds:", response.headers.get("X-RequestCounter-Reset"))
        return json.load(response)


data = get_json("/competitions/BSA/matches", "?season=2024&status=FINISHED")
print(data.keys())
```

## Plano gratis

No plano Free, a pagina de precos informa:

- 12 competicoes.
- Scores e schedules com atraso.
- Fixtures.
- League tables.
- 10 chamadas por minuto.

Na cobertura Free aparecem competicoes como Champions League, Primeira Liga,
Premier League, Eredivisie, Bundesliga, Ligue 1, Serie A italiana, La Liga,
Championship, Brasileirao Serie A, World Cup e European Championship.

## O que da para pegar

Comece por estas entidades:

| Dado | Endpoint | Para que serve |
| --- | --- | --- |
| Competicoes | `/competitions` | Descobrir competicoes disponiveis para sua conta. |
| Uma competicao | `/competitions/{codigo}` | Ver temporada atual, historico disponivel e metadados. |
| Jogos de uma competicao | `/competitions/{codigo}/matches` | Base principal para resultados, calendario e placares. |
| Classificacao | `/competitions/{codigo}/standings` | Tabela total, casa e fora em ligas. |
| Times da competicao | `/competitions/{codigo}/teams` | Lista de clubes por temporada. |
| Artilheiros | `/competitions/{codigo}/scorers` | Gols, assistencias e penaltis por jogador. Pode depender do plano. |
| Um time | `/teams/{id}` | Dados do clube e elenco quando disponivel no plano. |
| Jogos de um time | `/teams/{id}/matches` | Recorte por clube, casa/fora e periodo. |
| Um jogo | `/matches/{id}` | Detalhe de uma partida especifica. |
| Jogos por data | `/matches?date=YYYY-MM-DD` | Rodadas do dia, placares e agenda. |
| Pessoa | `/persons/{id}` | Jogadores, tecnicos e arbitros quando a API retornar esses ids. |

Codigos uteis:

- `BSA`: Campeonato Brasileiro Serie A.
- `BSB`: Campeonato Brasileiro Serie B.
- `PL`: Premier League.
- `BL1`: Bundesliga.
- `SA`: Serie A italiana.
- `PD`: La Liga.
- `FL1`: Ligue 1.
- `DED`: Eredivisie.
- `PPL`: Primeira Liga.
- `CL`: UEFA Champions League.
- `EC`: European Championship.
- `WC`: FIFA World Cup.

## Filtros mais uteis

Para jogos:

```text
?season=2024
?matchday=10
?status=FINISHED
?date=2026-06-29
?dateFrom=2026-06-01&dateTo=2026-07-01
```

Status comuns:

```text
SCHEDULED, TIMED, IN_PLAY, PAUSED, FINISHED, SUSPENDED, POSTPONED, CANCELLED, AWARDED
```

Para standings e scorers:

```text
?season=2024
?matchday=10
```

Para jogos de um time:

```text
?dateFrom=2026-01-01&dateTo=2026-12-31
?status=FINISHED
?venue=HOME
?limit=100
```

## Chamadas iniciais recomendadas

Use poucas chamadas primeiro, salvando o JSON bruto antes de transformar.

```bash
# 1. Ver o que sua conta enxerga
curl "https://api.football-data.org/v4/competitions" \
  -H "X-Auth-Token: $FOOTBALL_DATA_TOKEN"

# 2. Metadados do Brasileirao Serie A
curl "https://api.football-data.org/v4/competitions/BSA" \
  -H "X-Auth-Token: $FOOTBALL_DATA_TOKEN"

# 3. Jogos finalizados de uma temporada
curl "https://api.football-data.org/v4/competitions/BSA/matches?season=2024&status=FINISHED" \
  -H "X-Auth-Token: $FOOTBALL_DATA_TOKEN"

# 4. Classificacao
curl "https://api.football-data.org/v4/competitions/BSA/standings?season=2024" \
  -H "X-Auth-Token: $FOOTBALL_DATA_TOKEN"

# 5. Artilharia, se liberado no plano
curl "https://api.football-data.org/v4/competitions/BSA/scorers?season=2024" \
  -H "X-Auth-Token: $FOOTBALL_DATA_TOKEN"
```

## Limite e throttling

A API retorna headers uteis:

- `X-RequestsAvailable`: chamadas restantes antes do bloqueio.
- `X-RequestCounter-Reset`: segundos ate resetar o contador.
- `X-API-Version`: versao retornada.
- `X-Authenticated-Client`: cliente reconhecido.

Regra pratica: se `X-RequestsAvailable` estiver baixo, espere o valor de
`X-RequestCounter-Reset` antes de continuar. Evite loops tentando ids de 0 a
1000; busque primeiro listas oficiais e depois detalhe apenas ids encontrados.

## Como organizar os dados

Primeira versao simples:

```text
data/
  raw/
    competitions/
    matches/
    standings/
    teams/
    scorers/
  processed/
```

Sugestao de nome de arquivo:

```text
data/raw/matches/BSA_2024_FINISHED.json
data/raw/standings/BSA_2024.json
data/raw/scorers/BSA_2024.json
```

Depois, transformar para tabelas:

- `competitions`: `competition_id`, `code`, `name`, `area`, `type`.
- `teams`: `team_id`, `name`, `short_name`, `tla`, `founded`, `venue`.
- `matches`: `match_id`, `competition_code`, `season`, `utc_date`, `status`,
  `matchday`, `home_team_id`, `away_team_id`, `home_goals`, `away_goals`.
- `standings`: `competition_code`, `season`, `type`, `position`, `team_id`,
  `played_games`, `won`, `draw`, `lost`, `points`, `goals_for`,
  `goals_against`, `goal_difference`.
- `scorers`: `competition_code`, `season`, `player_id`, `team_id`, `goals`,
  `assists`, `penalties`.

## Ideias de analise

Depois que os dados estiverem limpos:

- Evolucao da tabela por rodada.
- Aproveitamento casa vs fora.
- Times acima/abaixo do esperado pela diferenca de gols.
- Sequencias de vitorias, empates e derrotas.
- Ataques mais eficientes: gols por jogo e gols fora de casa.
- Defesas mais solidas: gols sofridos por jogo.
- Comparacao entre artilharia e desempenho do time.
- Regularidade: variacao de posicao na tabela ao longo da temporada.
- Recorte Brasil vs Europa usando o mesmo pipeline.

## Referencias oficiais

- Quickstart: https://www.football-data.org/documentation/quickstart/
- API v4: https://docs.football-data.org/general/v4/index.html
- Lookup tables, headers, filtros e codigos: https://docs.football-data.org/general/v4/lookup_tables.html
- Coverage: https://www.football-data.org/coverage
- Pricing: https://www.football-data.org/pricing
