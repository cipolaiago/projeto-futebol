# Projeto Futebol

Este contexto descreve a linguagem usada para analisar dados publicos de futebol vindos da football-data.org.

## Language

**Scorer**:
Jogador retornado pelo endpoint de artilharia da API para uma competicao e temporada. Neste projeto, ele representa a base de jogadores ranqueados por participacao em gols, nao o elenco completo da competicao.
_Avoid_: jogador da Copa, convocado

**World Cup Team**:
Selecao que o scorer representa na Copa do Mundo.
_Avoid_: clube, time atual

**Goal Involvement**:
Soma de gols e assistencias do scorer na competicao consultada.
_Avoid_: participacao, contribuicao ofensiva
