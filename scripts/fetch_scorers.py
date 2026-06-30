import argparse
import json
import os
from datetime import date
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    import pandas as pd
except ModuleNotFoundError as error:
    raise SystemExit(
        "Instale as dependencias com: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
    ) from error


BASE_URL = "https://api.football-data.org/v4"
DEFAULT_OUTPUT = Path("data/processed/wc_2026_player_scorers.csv")
POSITIONS_PT = {
    "Defence": "Defesa",
    "Goalkeeper": "Goleiro",
    "Midfield": "Meio-campo",
    "Offence": "Ataque",
}
TEAMS_PT = {
    "Argentina": "Argentina",
    "Brazil": "Brasil",
    "Congo DR": "RD Congo",
    "France": "França",
    "Germany": "Alemanha",
    "Morocco": "Marrocos",
    "New Zealand": "Nova Zelândia",
    "Norway": "Noruega",
}


def number(value: object) -> int:
    return int(value or 0)


def header(headers: dict, *names: str) -> str | None:
    lower_headers = {key.lower(): value for key, value in headers.items()}
    for name in names:
        value = lower_headers.get(name.lower())
        if value is not None:
            return value
    return None


def age_on(birth_date: str | None, as_of: date) -> int | None:
    if not birth_date:
        return None
    born = date.fromisoformat(birth_date)
    return as_of.year - born.year - ((as_of.month, as_of.day) < (born.month, born.day))


def translate(value: str | None, translations: dict[str, str]) -> str | None:
    return translations.get(value, value)


def rate_limit_pause(headers: dict) -> None:
    left = header(headers, "X-RequestsAvailable", "X-RequestsAvailable-Minute")
    reset = header(headers, "X-RequestCounter-Reset")
    if left is not None and reset is not None and number(left) <= 1:
        time.sleep(number(reset) + 1)


def request_json(path: str, params: dict | None = None) -> tuple[dict, dict]:
    token = os.environ.get("FOOTBALL_DATA_TOKEN")
    if not token:
        raise SystemExit("Defina FOOTBALL_DATA_TOKEN antes de rodar.")

    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    request = urllib.request.Request(
        f"{BASE_URL}{path}{query}", headers={"X-Auth-Token": token}
    )

    for _ in range(2):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                headers = dict(response.headers.items())
                data = json.load(response)
                rate_limit_pause(headers)
                return data, headers
        except urllib.error.HTTPError as error:
            if error.code == 429:
                wait = (
                    number(
                        header(
                            dict(error.headers.items()),
                            "X-RequestCounter-Reset",
                            "Retry-After",
                        )
                    )
                    or 60
                )
                time.sleep(wait + 1)
                continue
            body = error.read().decode("utf-8", errors="replace")
            print(f"HTTP {error.code}: {body}", file=sys.stderr)
            raise SystemExit(1) from error

    raise SystemExit("Limite da API atingido. Tente novamente em alguns segundos.")


def fetch_scorers(competition: str, season: int) -> tuple[dict, dict]:
    return request_json(f"/competitions/{competition}/scorers", {"season": season})


def build_dataframe(scorers: list[dict], as_of: date) -> pd.DataFrame:
    rows = []
    for rank, scorer in enumerate(scorers, start=1):
        player = scorer.get("player") or {}
        team = scorer.get("team") or {}
        matches = number(scorer.get("playedMatches"))
        goals = number(scorer.get("goals"))
        assists = number(scorer.get("assists"))
        rows.append(
            {
                "classificacao": rank,
                "id_jogador": player.get("id"),
                "jogador": player.get("name"),
                "selecao": translate(team.get("name"), TEAMS_PT),
                "idade": age_on(player.get("dateOfBirth"), as_of),
                "posicao": translate(
                    player.get("position") or player.get("section"), POSITIONS_PT
                ),
                "jogos": matches,
                "gols": goals,
                "assistencias": assists,
                "participacoes_em_gols": goals + assists,
                "gols_por_jogo": round(goals / matches, 3) if matches else None,
            }
        )

    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False, encoding="utf-8-sig")


def self_check() -> None:
    as_of = date(2026, 6, 30)
    assert age_on("1987-06-24", as_of) == 39
    df = build_dataframe(
        [
            {
                "player": {
                    "id": 1,
                    "name": "A",
                    "dateOfBirth": "2000-01-01",
                    "section": "Offence",
                },
                "team": {"id": 10, "name": "Argentina"},
                "playedMatches": 2,
                "goals": 3,
                "assists": None,
            }
        ],
        as_of,
    )
    row = df.iloc[0]
    assert row["selecao"] == "Argentina"
    assert row["posicao"] == "Ataque"
    assert row["gols_por_jogo"] == 1.5
    assert row["participacoes_em_gols"] == 3


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--competition", default="WC")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        self_check()
        print("self_check: ok")
        return

    data, headers = fetch_scorers(args.competition, args.season)
    scorers = data.get("scorers", [])
    scorers.sort(
        key=lambda item: (number(item.get("goals")), number(item.get("assists"))),
        reverse=True,
    )
    df = build_dataframe(scorers, args.as_of)
    write_csv(df, args.output)

    print(
        f"competition: {data.get('competition', {}).get('name')} ({args.competition})"
    )
    print(f"season: {args.season}")
    print(f"scorers_found: {len(scorers)}")
    print(f"csv: {args.output}")
    print(
        f"requests_left: {header(headers, 'X-RequestsAvailable', 'X-RequestsAvailable-Minute')}"
    )
    print(f"reset_seconds: {header(headers, 'X-RequestCounter-Reset')}")
    print()
    print(df.head(args.limit).to_string(index=False))


if __name__ == "__main__":
    main()
