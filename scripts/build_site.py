from datetime import datetime, timezone
from html import escape
from pathlib import Path
import re
import shutil
import sys
import unicodedata

import pandas as pd


CSV_PATH = Path("data/processed/wc_2026_player_scorers.csv")
IMAGE_DIR = Path("images")
SITE_DIR = Path("site")
SITE_IMAGE_DIR = SITE_DIR / "images"
INDEX_PATH = SITE_DIR / "index.html"
IMAGE_EXTENSIONS = {".avif", ".jpeg", ".jpg", ".png", ".webp"}


def percent(value: float, max_value: float) -> float:
    if not max_value:
        return 0
    return round((value / max_value) * 100, 1)


def image_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def build_image_lookup() -> dict[str, str]:
    if not IMAGE_DIR.exists():
        return {}

    lookup = {}
    for path in sorted(IMAGE_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            lookup[image_key(path.stem)] = path.name
    return lookup


def copy_player_images() -> None:
    if not IMAGE_DIR.exists():
        return

    SITE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(IMAGE_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            shutil.copy2(path, SITE_IMAGE_DIR / path.name)


def image_for_player(player_name: object, image_lookup: dict[str, str]) -> str | None:
    name = str(player_name or "")
    keys = [image_key(name)]
    keys.extend(image_key(part) for part in name.replace("-", " ").split())

    for key in keys:
        if key in image_lookup:
            return f"images/{image_lookup[key]}"

    full_key = keys[0] if keys else ""
    for key, filename in image_lookup.items():
        if key and key in full_key:
            return f"images/{filename}"
    return None


def initials(player_name: object) -> str:
    parts = [part for part in re.split(r"\s+", str(player_name or "").strip()) if part]
    return escape("".join(part[0].upper() for part in parts[:2]) or "?")


def avatar_html(
    player_name: object, image_lookup: dict[str, str], class_name: str = "avatar"
) -> str:
    safe_name = escape(str(player_name or ""))
    src = image_for_player(player_name, image_lookup)
    if src:
        return (
            f'<img class="{class_name}" src="{escape(src)}" alt="Foto de {safe_name}" '
            'width="56" height="56" loading="lazy">'
        )
    return (
        f'<span class="{class_name} avatar-fallback" aria-hidden="true">'
        f"{initials(player_name)}</span>"
    )


def whole(value: object) -> str:
    if pd.isna(value):
        return "-"
    return str(int(value))


def decimal(value: object, places: int = 3) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.{places}f}"


def text(value: object) -> str:
    if pd.isna(value):
        return "-"
    return str(value)


def build_rows(df: pd.DataFrame, image_lookup: dict[str, str]) -> str:
    max_goals = float(df["gols"].max())
    rows = []
    for row in df.to_dict("records"):
        rank = int(row["classificacao"])
        goals_percent = percent(float(row["gols"]), max_goals)
        rank_class = f" rank-{rank}" if rank <= 3 else ""
        rows.append(
            f"""
            <tr class="ranking-row{rank_class}">
              <td><span class="rank-badge{rank_class}">{rank}</span></td>
              <td class="player-cell">
                <div class="player-card">
                  {avatar_html(row["jogador"], image_lookup)}
                  <div>
                    <strong>{escape(text(row["jogador"]))}</strong>
                    <span>{escape(text(row["posicao"]))} &middot; {whole(row["idade"])} anos</span>
                  </div>
                </div>
              </td>
              <td>{escape(text(row["selecao"]))}</td>
              <td>{whole(row["jogos"])}</td>
              <td>
                <div class="metric">
                  <strong>{whole(row["gols"])}</strong>
                  <div class="bar"><i style="width: {goals_percent}%"></i></div>
                </div>
              </td>
              <td>{whole(row["assistencias"])}</td>
              <td>{whole(row["participacoes_em_gols"])}</td>
              <td>{decimal(row["gols_por_jogo"])}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def build_site() -> None:
    df = pd.read_csv(CSV_PATH)
    image_lookup = build_image_lookup()
    leader = df.iloc[0]
    generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    table_rows = build_rows(df, image_lookup)
    leader_avatar = avatar_html(leader["jogador"], image_lookup, "avatar leader-photo")

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artilharia da Copa 2026</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07120e;
      --bg-2: #111812;
      --panel: #f6f4e8;
      --panel-strong: #ffffff;
      --ink: #f8fafc;
      --panel-ink: #17201b;
      --muted: #9fb4aa;
      --panel-muted: #5a6760;
      --line: rgba(255, 255, 255, .14);
      --panel-line: #d9dece;
      --green: #22c55e;
      --gold: #f6c453;
      --blue: #38bdf8;
      --red: #ef4444;
      --shadow: 0 20px 50px rgba(0, 0, 0, .24);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        linear-gradient(180deg, var(--bg) 0, #0d1c16 430px, #eef1e4 430px, #eef1e4 100%);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    .wrap {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
    }}
    header {{
      position: relative;
      overflow: hidden;
      border-bottom: 1px solid rgba(255, 255, 255, .12);
      background:
        linear-gradient(90deg, rgba(34, 197, 94, .18), transparent 42%, rgba(56, 189, 248, .12)),
        repeating-linear-gradient(90deg, rgba(255, 255, 255, .08) 0 1px, transparent 1px 90px),
        repeating-linear-gradient(0deg, rgba(255, 255, 255, .05) 0 1px, transparent 1px 72px),
        var(--bg);
    }}
    header::after {{
      content: "";
      position: absolute;
      inset: 28px auto 28px 50%;
      width: min(360px, 45vw);
      transform: translateX(-50%);
      border: 2px solid rgba(255, 255, 255, .12);
      border-radius: 8px;
      pointer-events: none;
    }}
    .hero {{
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(280px, 380px);
      gap: 28px;
      align-items: end;
      padding: 42px 0 32px;
      z-index: 1;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 5px 10px;
      border: 1px solid rgba(246, 196, 83, .45);
      border-radius: 8px;
      background: rgba(246, 196, 83, .12);
      color: #ffe08a;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    h1 {{
      max-width: 760px;
      margin: 14px 0 0;
      font-size: clamp(34px, 6vw, 68px);
      letter-spacing: 0;
      line-height: .98;
    }}
    .sub {{
      max-width: 760px;
      margin: 16px 0 0;
      color: #d6e4dd;
      font-size: 17px;
      line-height: 1.6;
    }}
    .summary {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      margin-top: 24px;
    }}
    .stat {{
      min-height: 92px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, .08);
      padding: 16px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, .06);
    }}
    .stat strong {{
      display: block;
      color: #ffffff;
      font-size: 26px;
      line-height: 1.1;
    }}
    .stat span {{
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }}
    .leader-panel {{
      border: 1px solid rgba(255, 255, 255, .16);
      border-radius: 8px;
      background: rgba(7, 18, 14, .78);
      box-shadow: var(--shadow);
      padding: 18px;
    }}
    .leader-card {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    .leader-kicker {{
      color: var(--gold);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    .leader-name {{
      display: block;
      margin-top: 4px;
      color: #ffffff;
      font-size: 26px;
      font-weight: 900;
      line-height: 1.05;
    }}
    .leader-meta {{
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: 14px;
    }}
    .leader-score {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 18px;
    }}
    .leader-score div {{
      border-radius: 8px;
      background: rgba(255, 255, 255, .08);
      padding: 12px;
    }}
    .leader-score strong {{
      display: block;
      color: #ffffff;
      font-size: 24px;
      line-height: 1;
    }}
    .leader-score span {{
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
    }}
    main {{
      padding: 24px 0 42px;
      color: var(--panel-ink);
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
    }}
    .toolbar h2 {{
      margin: 0;
      font-size: 22px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .updated {{
      color: var(--panel-muted);
      font-size: 14px;
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--panel-line);
      border-radius: 8px;
      background: var(--panel-strong);
      box-shadow: 0 18px 42px rgba(28, 38, 31, .12);
    }}
    table {{
      width: 100%;
      min-width: 940px;
      border-collapse: collapse;
    }}
    caption {{
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }}
    th, td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--panel-line);
      text-align: left;
      white-space: nowrap;
      vertical-align: middle;
    }}
    th {{
      position: sticky;
      top: 0;
      z-index: 1;
      background: #e7ebd8;
      color: #314139;
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    td {{
      font-size: 14px;
    }}
    tbody tr {{
      transition: background-color 180ms ease;
    }}
    tbody tr:hover {{
      background: #f7f8ef;
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    .rank-badge {{
      display: inline-grid;
      place-items: center;
      width: 34px;
      height: 34px;
      border-radius: 8px;
      background: #edf1e3;
      color: #2d3933;
      font-weight: 900;
      font-variant-numeric: tabular-nums;
    }}
    .rank-badge.rank-1 {{
      background: var(--gold);
      color: #2f2500;
    }}
    .rank-badge.rank-2 {{
      background: #d8dde4;
      color: #26313a;
    }}
    .rank-badge.rank-3 {{
      background: #c98b5a;
      color: #2d1707;
    }}
    .player-cell {{
      min-width: 280px;
    }}
    .player-card {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .player-card strong {{
      display: block;
      color: #17201b;
      font-size: 15px;
      line-height: 1.2;
    }}
    .player-card span {{
      display: block;
      margin-top: 4px;
      color: var(--panel-muted);
      font-size: 13px;
    }}
    .avatar {{
      flex: 0 0 auto;
      width: 56px;
      height: 56px;
      border: 2px solid #ffffff;
      border-radius: 8px;
      background: #dfe7d4;
      box-shadow: 0 8px 18px rgba(20, 31, 25, .16);
      object-fit: cover;
      object-position: top center;
    }}
    .leader-photo {{
      width: 84px;
      height: 84px;
      border-color: rgba(246, 196, 83, .9);
      box-shadow: 0 14px 28px rgba(0, 0, 0, .32);
    }}
    .avatar-fallback {{
      display: inline-grid;
      place-items: center;
      color: #193625;
      font-weight: 900;
    }}
    .metric {{
      display: grid;
      align-items: center;
      grid-template-columns: 30px 1fr;
      gap: 10px;
      min-width: 150px;
    }}
    .metric strong {{
      font-size: 16px;
      font-variant-numeric: tabular-nums;
    }}
    .bar {{
      height: 10px;
      overflow: hidden;
      border-radius: 999px;
      background: #e4e8d8;
    }}
    .bar i {{
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--green), var(--blue), var(--gold));
    }}
    footer {{
      padding: 0 0 30px;
      color: #5f6d65;
      font-size: 13px;
    }}
    @media (max-width: 760px) {{
      .wrap {{
        width: min(100% - 24px, 1180px);
      }}
      .hero {{
        grid-template-columns: 1fr;
        padding-top: 30px;
      }}
      .leader-panel {{
        max-width: 460px;
      }}
      .toolbar {{
        display: block;
      }}
      .updated {{
        margin-top: 6px;
      }}
      th, td {{
        padding: 12px;
      }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        transition-duration: .01ms !important;
        scroll-behavior: auto !important;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap hero">
      <div>
        <span class="eyebrow">Ranking ao vivo</span>
        <h1>Artilharia da Copa 2026</h1>
        <p class="sub">Ranking de jogadores com gols, assist&ecirc;ncias e participa&ccedil;&atilde;o direta em gols. Fotos dos atletas, barras de desempenho e lideran&ccedil;a em destaque para leitura r&aacute;pida.</p>
        <div class="summary">
          <div class="stat"><strong>{len(df)}</strong><span>jogadores no ranking</span></div>
          <div class="stat"><strong>{whole(df["gols"].sum())}</strong><span>gols somados na tabela</span></div>
          <div class="stat"><strong>{whole(df["assistencias"].sum())}</strong><span>assist&ecirc;ncias somadas</span></div>
        </div>
      </div>
      <aside class="leader-panel" aria-label="Lider do ranking">
        <div class="leader-card">
          {leader_avatar}
          <div>
            <span class="leader-kicker">L&iacute;der</span>
            <strong class="leader-name">{escape(text(leader["jogador"]))}</strong>
            <span class="leader-meta">{escape(text(leader["selecao"]))} &middot; {escape(text(leader["posicao"]))}</span>
          </div>
        </div>
        <div class="leader-score">
          <div><strong>{whole(leader["gols"])}</strong><span>gols</span></div>
          <div><strong>{decimal(leader["gols_por_jogo"])}</strong><span>gols por jogo</span></div>
        </div>
      </aside>
    </div>
  </header>
  <main class="wrap">
    <div class="toolbar">
      <h2>Classifica&ccedil;&atilde;o dos artilheiros</h2>
      <div class="updated">Atualizado em {generated_at}</div>
    </div>
    <div class="table-wrap">
      <table>
        <caption>Ranking completo de artilheiros da Copa 2026</caption>
        <thead>
          <tr>
            <th>#</th>
            <th>Jogador</th>
            <th>Sele&ccedil;&atilde;o</th>
            <th>Jogos</th>
            <th>Gols</th>
            <th>Assist&ecirc;ncias</th>
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
  <footer class="wrap">Fonte: football-data.org API v4. Projeto pessoal para an&aacute;lise de dados de futebol.</footer>
</body>
</html>
"""

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    copy_player_images()
    INDEX_PATH.write_text(html, encoding="utf-8")


def self_check() -> None:
    lookup = {
        "mbappe": "mbappe.jpg",
        "viniciusjunior": "viniciusjunior.jpg",
        "kaihavertz": "kai_havertz.jpg",
    }
    assert image_for_player("Kylian Mbappe", lookup) == "images/mbappe.jpg"
    assert image_for_player("Vinicius Junior", lookup) == "images/viniciusjunior.jpg"
    assert image_for_player("Kai Havertz", lookup) == "images/kai_havertz.jpg"
    assert initials("Kylian Mbappe") == "KM"
    print("self_check: ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        build_site()
