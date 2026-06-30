from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd


CSV_PATH = Path("data/processed/wc_2026_player_scorers.csv")
SITE_DIR = Path("site")
INDEX_PATH = SITE_DIR / "index.html"


def percent(value: float, max_value: float) -> float:
    if not max_value:
        return 0
    return round((value / max_value) * 100, 1)


def build_rows(df: pd.DataFrame) -> str:
    max_goals = float(df["gols"].max())
    rows = []
    for row in df.to_dict("records"):
        goals_percent = percent(float(row["gols"]), max_goals)
        rows.append(
            f"""
            <tr>
              <td>{row["classificacao"]}</td>
              <td class="player">{escape(row["jogador"])}</td>
              <td>{escape(row["selecao"])}</td>
              <td>{row["idade"]}</td>
              <td>{escape(row["posicao"])}</td>
              <td>{row["jogos"]}</td>
              <td>
                <div class="metric">
                  <span>{row["gols"]}</span>
                  <div class="bar"><i style="width: {goals_percent}%"></i></div>
                </div>
              </td>
              <td>{row["assistencias"]}</td>
              <td>{row["participacoes_em_gols"]}</td>
              <td>{row["gols_por_jogo"]:.3f}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def build_site() -> None:
    df = pd.read_csv(CSV_PATH)
    leader = df.iloc[0]
    generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    table_rows = build_rows(df)

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artilharia da Copa 2026</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f2;
      --ink: #18211f;
      --muted: #5b6762;
      --line: #d8ded8;
      --panel: #ffffff;
      --accent: #0b7a53;
      --accent-2: #c83b2f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background:
        linear-gradient(90deg, rgba(11, 122, 83, .12), rgba(200, 59, 47, .10)),
        repeating-linear-gradient(90deg, rgba(11, 122, 83, .08) 0 1px, transparent 1px 80px),
        var(--panel);
    }}
    .wrap {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
    }}
    .hero {{
      display: grid;
      gap: 20px;
      grid-template-columns: 1fr;
      padding: 32px 0 24px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(28px, 5vw, 48px);
      letter-spacing: 0;
      line-height: 1.05;
    }}
    .sub {{
      max-width: 760px;
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.5;
    }}
    .summary {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      margin-top: 22px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, .8);
      padding: 14px;
    }}
    .stat strong {{
      display: block;
      font-size: 24px;
      line-height: 1.1;
    }}
    .stat span {{
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 13px;
    }}
    main {{ padding: 24px 0 40px; }}
    .toolbar {{
      margin-bottom: 14px;
    }}
    .updated {{ color: var(--muted); font-size: 14px; }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 880px;
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
    }}
    th {{
      background: #edf2ee;
      color: #31413b;
      font-size: 12px;
      text-transform: uppercase;
    }}
    td {{ font-size: 14px; }}
    tr:last-child td {{ border-bottom: 0; }}
    .player {{ font-weight: 750; }}
    .metric {{
      display: grid;
      align-items: center;
      grid-template-columns: 28px 1fr;
      gap: 8px;
      min-width: 120px;
    }}
    .bar {{
      height: 8px;
      overflow: hidden;
      border-radius: 999px;
      background: #e6e9e4;
    }}
    .bar i {{
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
    }}
    footer {{
      padding: 18px 0 28px;
      color: var(--muted);
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap hero">
      <div>
        <h1>Artilharia da Copa 2026</h1>
        <p class="sub">Ranking de jogadores com gols, assistências e participação direta em gols. Dados atualizados pela football-data.org e publicados automaticamente pelo GitHub Pages.</p>
        <div class="summary">
          <div class="stat"><strong>{len(df)}</strong><span>jogadores no ranking</span></div>
          <div class="stat"><strong>{escape(leader["jogador"])}</strong><span>líder: {leader["gols"]} gols</span></div>
          <div class="stat"><strong>{int(df["gols"].sum())}</strong><span>gols somados na tabela</span></div>
          <div class="stat"><strong>{int(df["assistencias"].sum())}</strong><span>assistências somadas</span></div>
        </div>
      </div>
    </div>
  </header>
  <main class="wrap">
    <div class="toolbar">
      <div class="updated">Atualizado em {generated_at}</div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Jogador</th>
            <th>Seleção</th>
            <th>Idade</th>
            <th>Posição</th>
            <th>Jogos</th>
            <th>Gols</th>
            <th>Assistências</th>
            <th>Part. em gols</th>
            <th>Gols/jogo</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </div>
  </main>
  <footer class="wrap">Fonte: football-data.org API v4. Projeto pessoal para análise de dados de futebol.</footer>
</body>
</html>
"""

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    build_site()
