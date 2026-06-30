# Projeto Futebol

Tabela publica da artilharia da Copa 2026, atualizada pela API da football-data.org e publicada no GitHub Pages.

Site: https://cipolaiago.github.io/projeto-futebol/

O workflow tambem roda automaticamente a cada hora.

## Arquivos Principais

- `scripts/fetch_scorers.py`: busca os dados da API e gera o CSV.
- `scripts/build_site.py`: gera a pagina estatica em `site/`.
- `.github/workflows/update-site.yml`: atualizacao e deploy no GitHub Pages.
