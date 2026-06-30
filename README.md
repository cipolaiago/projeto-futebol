# Projeto Futebol

Tabela publica da artilharia da Copa 2026, atualizada pela API da football-data.org e publicada no GitHub Pages.

Site: https://cipolaiago.github.io/projeto-futebol/

## Rodar Localmente

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:FOOTBALL_DATA_TOKEN = "seu_token"
.\.venv\Scripts\python.exe scripts\fetch_scorers.py --competition WC --season 2026
.\.venv\Scripts\python.exe scripts\build_site.py
```

Abra `site/index.html` no navegador.

`data/` e `site/` sao gerados pelos scripts e nao precisam ir para o GitHub.

## Publicar

No GitHub:

1. `Settings > Secrets and variables > Actions`
2. Crie `FOOTBALL_DATA_TOKEN`
3. `Settings > Pages > Build and deployment > Source`
4. Escolha `GitHub Actions`
5. Rode `Actions > Update GitHub Pages > Run workflow`

O workflow tambem roda automaticamente a cada hora.

## Arquivos Principais

- `scripts/fetch_scorers.py`: busca os dados da API e gera o CSV.
- `scripts/build_site.py`: gera a pagina estatica em `site/`.
- `.github/workflows/update-site.yml`: atualizacao e deploy no GitHub Pages.
