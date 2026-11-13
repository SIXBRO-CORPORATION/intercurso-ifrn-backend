# Domínio

## Modelo de acesso (ADR004)
Leitura pública, ação autenticada. Públicos: `GET /api/season/active`, `GET /api/modality/`, `GET /api/match/`, `GET /api/match/{id}` (sem `matricula`), canais SSE via ticket. Ações exigem usuário autenticado; gestão (temporada, modalidade, chaveamento, partida, aprovação de equipe) exige monitor.

## Casos de uso (`docs/planning/spec/`)
| Grupo | UCs |
|---|---|
| Temporadas | 001 criar, 002 gerenciar, 003 finalizar |
| Modalidades | 004 cadastrar |
| Equipes | 005 criar, 006 convite, 007 membros, 008 submeter, 009 aprovar, 010 doação |
| Chaveamento | 011 criar, 012 gerenciar |
| Partidas | 013 iniciar, 014 evento, 015 finalizar, 017 corrigir evento |
| Interface | 016 visualizar partida |

## ADRs (`docs/planning/adr/`)
001 cronômetro no servidor, 002 normalização de modalidade, 003 SSE, 004 modelo de acesso, 005 push.

Enums de domínio: `domain/enums/` (status de temporada/equipe/partida/chaveamento, papéis, tipos de evento, etc.).
