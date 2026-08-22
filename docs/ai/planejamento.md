# Plano de Execução — Intercurso IFRN Backend

> Baseado na leitura dos 18 casos de uso em `docs/` e na análise do código-fonte atual do repositório `SIXBRO-CORPORATION/intercurso-ifrn-backend` (branch `main`).
>
> **Atualizado em 2026-08-22** após a conclusão do UC015 (Finalizar Partida) dentro da Fase 5, entregue em duas rodadas (patch 1 — avanço automático no chaveamento + fluxo principal; patch 2 — disputa de pênaltis). O diagnóstico e a tabela abaixo refletem o estado real do código nesta data, não mais o estado descrito nas versões anteriores deste plano.

---

## 1. Diagnóstico do estado atual

O projeto segue uma arquitetura em camadas (hexagonal/ports & adapters): `domain` → `core` (ports/interfaces) → `business` (adapters/casos de uso) → `persistence` (SQLAlchemy) → `web` (FastAPI). O padrão de caso de uso usa `Command`/`Context` (`core/command.py`, `core/context.py`).

**O build está destravado.** A Fase 0 foi concluída: `core/business/team/` e `business/team/` foram implementados (`create_team_port/adapter`, `approve_team_port/adapter`, `confirm_donation_port/adapter`), a aplicação sobe sem `ImportError` e a pasta `tests/` existe e está em uso.

**Padrão geral encontrado (revisado):**
- **Domain + Persistence (models, mappers, adapters, ports):** construídos para praticamente todas as entidades do sistema (Season, Modality, Team, Bracket, Match, etc.) — trabalho de infraestrutura bem avançado.
- **Business (casos de uso reais):** implementado para Autenticação, Usuário (criar/buscar/atualizar perfil), **Temporada (UC001, UC002 e UC003 completos)**, **Modalidade (UC004 completo)**, **Equipe (UC005 a UC010 completos)**, **Chaveamento (UC011 e UC012 completos)** e, dentro de Partida, **UC013 (Iniciar Partida), UC014 (Registrar Evento) e UC015 (Finalizar Partida) completos**: gol/ponto, cartão amarelo/vermelho com expulsão automática no 2º amarelo ou vermelho direto, pausar/retomar cronômetro, encerrar/iniciar período, encerrar set (vôlei, com sugestão automática de fim de partida ao atingir os sets necessários), finalizar partida com avanço automático no chaveamento (vencedor → próxima fase, perdedor de semifinal → 3º lugar) e disputa de pênaltis completa (iniciar/registrar cobrança/encerrar) para o desempate em mata-mata. UC017 segue sem lógica de negócio.
- **Web (controllers/rotas):** `auth_controller`, `user_controller`, `season_controller` e `modality_controller` funcionais e registrados em `main.py`. `team_controller` completo para o ciclo de vida do time: criar, entrar via convite, selecionar capitão, remover membro, sair do time, submeter para aprovação, aprovar e confirmar doação. `bracket_controller` completo para criar chaveamento (com preview de configuração), re-sortear, editar e deletar partidas. `match_controller` cobre início de partida, todos os sub-fluxos do UC014 (`POST /api/match/{match_id}/goal`, `/card`, `/clock/pause`, `/clock/resume`, `/period/end`, `/period/start`, `/set/end`) e o UC015 (`POST /api/match/{match_id}/finish`, `/penalty-shootout/start`, `/penalty-shootout/kick`, `/penalty-shootout/end`), todos exigindo ator Monitor e devolvendo a mesma resposta rica (`MatchManagementResponse`) usada pelo `start`.
- **Testes:** `tests/unit/business` cobre os adapters de `season`, `modality`, `team` (parcialmente), `bracket` (motor de sorteio + os 4 adapters, agora também o encadeamento de `next_match_id`) e `match` — 224 testes no total da suíte, sendo 45 no módulo `match` (`start_match`, UC014 completo, `finish_match` e os 3 adapters de pênaltis do UC015). Ainda não há testes de `tests/integration` nem `tests/e2e`.
- **Jobs automáticos (UC001/UC002):** implementados via APScheduler (`scheduling/configuration/scheduler.py` + `scheduling/jobs/season_scheduler_jobs.py`), rodando a cada 1 minuto para abrir/fechar inscrições automaticamente.
- **Auditoria:** existe infraestrutura própria (`domain/audit/audit_log.py`, `core/business/audit/audit_logger.py`, tabela `logs`) e já é usada em `season`, `team`, `bracket`, no `start_match_adapter` (UC013) e agora no UC015 (`AuditAction.MATCH_FINISHED` em `finish_match_adapter`/`end_penalty_shootout_adapter`, `AuditAction.PENALTY_SHOOTOUT_STARTED` em `start_penalty_shootout_adapter`). **Os sete adapters do UC014 (gol, cartão, pausar/retomar cronômetro, período, set) continuam sem chamar o `AuditLogger`** — decisão consciente tomada no início da rodada do UC015 (fechar esse débito específico em uma rodada separada, dedicada só a isso, em vez de misturar com o UC015) — RN41-42 do UC014 segue, portanto, incompleta.
- **UC018 (Reportar Jogador):** não existe absolutamente nada — nem domínio, nem persistência, nem enum de status.
- **UC016 (Visualizar Partida em Tempo Real):** nenhuma infraestrutura de tempo real implementada ainda, mas a decisão de transporte já foi tomada no [ADR 0003](../adr/ADR003_EnvioDeEventos.md): **SSE**, não WebSocket (o documento do UC usa a palavra "WebSocket", mas o ADR argumenta que o canal é unidirecional servidor→aluno, então SSE via `StreamingResponse`/`EventSource` é suficiente e mais simples). Nenhuma ocorrência de `websocket` ou de `sse-starlette`/`EventSourceResponse` no código ainda — é só a decisão, a implementação (Fase 6) não começou.

### Tabela: Casos de uso × estado das camadas

| UC | Caso de uso | Domain | Persistence | Business | Web/API |
|----|---|:---:|:---:|:---:|:---:|
| 001 | Criar Temporada | ✅ | ✅ | ✅ | ✅ |
| 002 | Gerenciar Temporada | ✅ | ✅ | ✅ | ✅ |
| 003 | Finalizar Temporada | ✅ | ✅ | ✅ | ✅ |
| 004 | Cadastrar Modalidade | ✅ | ✅ | ✅ | ✅ |
| 005 | Criar Equipe | ✅ | ✅ | ✅ | ✅ |
| 006 | Entrar via Convite | ✅ | ✅ | ✅ | ✅ |
| 007 | Gerenciar Membros | ✅ | ✅ | ✅ | ✅ |
| 008 | Submeter Equipe | ✅ | ✅ | ✅ | ✅ |
| 009 | Aprovar Equipe | ✅ | ✅ | ✅ | ✅ |
| 010 | Confirmar Doação | ✅ | ✅ | ✅ | ✅ |
| 011 | Criar Chaveamento | ✅ | ✅ | ✅ | ✅ |
| 012 | Gerenciar Chaveamento | ✅ | ✅ | ✅ | ✅ |
| 013 | Iniciar Partida | ✅ | ✅ | ✅ | ✅ |
| 014 | Registrar Evento | ✅ | ✅ | ✅ | ✅ |
| 015 | Finalizar Partida | ✅ | ✅ | ✅ | ✅ |
| 016 | Visualizar Partida (tempo real) | ✅ (parcial) | ✅ | ❌ | ❌ (sem WebSocket) |
| 017 | Corrigir Evento | ✅ | ✅ | ❌ | ❌ |
| 018 | Reportar Jogador | ❌ | ❌ | ❌ | ❌ |

**Legenda:** ✅ implementado · ⚠️ parcial/quebrado · ❌ inexistente

---

## 2. Estratégia geral

1. **Nada podia ser entregue antes de destravar o build — isso já foi feito na Fase 0.** A partir de agora a prioridade é seguir a ordem funcional das fases.
2. Implementar a camada `business` seguindo rigorosamente o padrão já estabelecido (`Command[R]` + `Context`, ports em `core/business/<módulo>/*_port.py`, adapters em `business/<módulo>/*_adapter.py`), reaproveitando o que já existe em `core/persistence` e `domain`.
3. Seguir a ordem de dependência funcional entre os casos de uso (Temporada → Modalidade → Equipe → Chaveamento → Partida → Tempo real → Reportes), que é também a ordem sugerida pela numeração dos próprios documentos em `docs/`.
4. Criar a pasta `tests/` desde a Fase 0, com pelo menos testes unitários por caso de uso à medida que ele é implementado (o projeto já está configurado para isso, só falta o conteúdo).

---

## 3. Fases de execução

### Fase 0 — Destravar o build ✅ CONCLUÍDA
- Criados `core/business/team/` com os ports que faltavam: `create_team_port.py`, `approve_team_port.py`, `confirm_donation_port.py`.
- Criados `business/team/` com os adapters correspondentes: `create_team_adapter.py`, `approve_team_adapter.py`, `confirm_donation_adapter.py`, implementando as regras descritas em UC005, UC009 e UC010.
- Aplicação sobe sem `ImportError` (`web.main:app`), `/health` responde.
- Estrutura `tests/unit` (com subpastas por módulo) criada e em uso.

### Fase 1 — Gestão de Temporadas (UC001, UC002, UC003) ✅ CONCLUÍDA
- `core/business/season/`: `create_season_port`, `manage_season_port`, `close_registration_port`, `reopen_registration_port`, `get_season_details_port` e `finish_season_port` implementados.
- `business/season/`: adapters cobrindo as regras de negócio de cada UC — transições DRAFT → REGISTRATION_OPEN → REGISTRATION_CLOSED → IN_PROGRESS → FINISHED, edição de datas, encerramento antecipado, reabertura de inscrições e finalização com validação de nome de confirmação (UC003) + desativação dos convites de time (`token_active = False`) ao finalizar.
- Job automático de abertura/encerramento de inscrições implementado com **APScheduler** (`scheduling/configuration/scheduler.py`, `scheduling/jobs/season_scheduler_jobs.py`), com polling a cada 1 minuto.
- `web/controllers/season_controller.py` completo, com as rotas `POST /api/season/`, `GET /api/season/{id}`, `PATCH /api/season/{id}/dates`, `POST /api/season/{id}/close-registration`, `POST /api/season/{id}/reopen-registration` e `POST /api/season/{id}/finish`, além dos respectivos request/response models e mapper.
- Testes unitários dos adapters em `tests/unit/business/season/` (create, manage, close, reopen, details e finish).
- **Débito técnico assumido (documentado em TODOs no código):** validação de "todos os jogos finalizados" antes de encerrar a temporada (UC003, regra futura — depende da Fase 5) e registro de auditoria das operações (depende de infraestrutura de auditoria ainda inexistente).

### Fase 2 — Gestão de Modalidades (UC004) ✅ CONCLUÍDA
- `core/business/modality/create_modality_port.py` + adapter, com validações: nome duplicado, `min_members` ≥ 1, `max_members` ≥ `min_members`.
- `web/controllers/modality_controller.py`.
- Testes unitários em `tests/unit/business/modality/`.

### Fase 3 — Completar Gestão de Equipes (UC006, UC007, UC008) ✅ CONCLUÍDA
UC005/009/010 já concluídos nas Fases 0/1. Nesta fase:
- UC006 — Entrar via Convite: `join_team_via_invite_port/adapter` (validação de token/`token_active`, time em DRAFT, temporada ativa em REGISTRATION_OPEN dentro do período de inscrição, limite máximo de membros da modalidade, aluno não estar em outro time da mesma modalidade/temporada, marca `atleta = true` no usuário).
- UC007 — Gerenciar Membros: `select_captain_port/adapter`, `remove_member_port/adapter` e `leave_team_port/adapter`.
  - Capitão é controlado exclusivamente via `team.captain_id` (o campo `TeamMember.role` não foi alterado e continua distinguindo apenas OWNER/MEMBER), permitindo o owner acumular os papéis de dono e capitão sem conflito.
  - Remoção de membro aceita dois atores no mesmo endpoint: owner (somente com time em DRAFT) ou monitor (em qualquer status do time), decidido dentro do próprio adapter a partir do `role` do usuário autenticado.
  - Saída voluntária do time bloqueada para o owner e restrita a times em DRAFT.
  - Ambos os fluxos liberam `team.captain_id` quando o membro removido/saindo era o capitão, e desmarcam `atleta = false` no usuário quando ele não pertence a mais nenhum outro time.
  - Endpoint de confirmação de doação (UC010) alterado para identificar o membro alvo por `user_id` em vez de matrícula, padronizando a identificação por ID nas rotas de membro.
  - Adicionado método `delete` (soft delete) em `TeamMemberRepositoryPort`/adapter, seguindo o mesmo padrão já usado em `MatchRepositoryPort.delete_by_bracket`.
- UC008 — Submeter Equipe: `submit_team_port/adapter` — valida owner, time em DRAFT, temporada ativa (`find_active_season`) igual à do time e em REGISTRATION_OPEN dentro do período, mínimo de membros da modalidade; transição para `TeamStatus.SUBMITTED`, `token_active = False`, `submmited_at = now()` e normalização do `donation_status` dos membros para `PENDING_DONATION`.
- `team_controller.py` ampliado com as novas rotas: `PATCH /{team_id}/members/{user_id}/captain`, `DELETE /{team_id}/members/{user_id}`, `DELETE /{team_id}/leave`, `PATCH /{team_id}/submit`, além da alteração de `confirm-donation` para usar `user_id`.
- **Débito técnico assumido (documentado em TODOs no código, mesmo padrão das fases anteriores):** registro de auditoria das operações (autor, data/hora, ação) e notificação ao monitor na submissão — ambos dependem de infraestrutura ainda inexistente no projeto.
- **Pendente:** testes unitários de UC006, UC007 e UC008 (decisão consciente de adiar para focar no código nesta rodada); ampliar cobertura de UC005/009/010 (ainda sem testes próprios, conforme já apontado nas fases anteriores).

### Fase 4 — Gestão de Chaveamento (UC011, UC012) ✅ CONCLUÍDA
- `core/business/bracket/` + `business/bracket/`: um port/adapter por ação, seguindo o padrão granular já usado em `team` — `get_bracket_config_suggestion_port/adapter` (preview, GET, não persiste), `create_bracket_port/adapter` (UC011), `resort_bracket_port/adapter`, `update_match_port/adapter` e `delete_match_port/adapter` (UC012).
- `business/bracket/engine/`: motor de sorteio puro (sem I/O), reaproveitado por criação, re-sorteio e preview:
  - `draw_engine.py` — gera a árvore de mata-mata (BYE resolvido automaticamente, `match_type` SEMIFINAL/FINAL/THIRD_PLACE definidos pela posição na árvore), rodízio de grupos (método do círculo) e distribuição de grupos.
  - `config_suggester.py` — sugestão de configuração padrão por formato e validação da configuração informada pelo monitor.
  - Regras fechadas com o time antes da implementação: KNOCKOUT preenche com múltiplos BYEs até a próxima potência de 2; TRIANGULAR só habilitado com exatamente 3 times aprovados; GROUP_STAGE_KNOCKOUT sempre sugere um total de classificados que já é potência de 2 (evitando BYE na fase de mata-mata pós-grupos).
- `core/persistence`: `TeamRepositoryPort.find_approved_teams_by_season_and_modality` e `MatchRepositoryPort.delete` (soft delete de partida individual) adicionados — extensões diretas do padrão já existente, implementadas nos respectivos adapters.
- `web/controllers/bracket_controller.py`: `GET /api/bracket/preview`, `POST /api/bracket/`, `POST /api/bracket/{bracket_id}/resort`, `PATCH /api/bracket/match/{match_id}`, `DELETE /api/bracket/match/{match_id}`.
- Testes unitários em `tests/unit/business/bracket/` (50 testes): motor de sorteio (KNOCKOUT com/sem potência de 2, GROUP_STAGE_KNOCKOUT, ROUND_ROBIN, TRIANGULAR) e os 4 adapters com mocks das ports.
- **Débito técnico assumido (documentado em TODOs no código, mesmo padrão das fases anteriores):** notificações aos alunos e registro de auditoria dependem de infraestrutura ainda inexistente no projeto.
- **Débito técnico específico desta fase (documentado no topo do `bracket_controller.py`):** endpoints de consulta (`GET` de detalhe do bracket com grupos/partidas, `GET` de lista de brackets da temporada, `GET` de lista de partidas) não foram implementados nesta rodada — o foco foi a camada de escrita (UC011/UC012 são, em essência, casos de uso de criação/edição). Ficam para uma rodada futura de endpoints de leitura para o front.
- **Observação para a Fase 5 (RESOLVIDA no UC015):** `Match` não possuía campo de posição/rodada na árvore de chaveamento. A Fase 5 definiu a estratégia — coluna persistida `next_match_id` (ver detalhes na seção do UC015 abaixo) — no lugar de recalcular a posição a partir do sorteio a cada finalização.

### Fase 5 — Gestão de Partidas (UC013 ✅ CONCLUÍDA · UC014 ✅ CONCLUÍDA · UC015 ✅ CONCLUÍDA · UC017 pendente)
- **Estratégia de rastreamento de monitor (decisão tomada na rodada do UC013):** foi criada uma coluna dedicada `monitor_id` (FK para `users`, nullable) em `matches`, em vez de inferir o monitor responsável a partir de outra tabela. `MatchRepositoryPort` ganhou `find_in_progress_by_monitor(monitor_id)`, usada para aplicar a regra de negócio 4 do UC013 ("apenas uma partida IN_PROGRESS por monitor").
- `core/business/match/start_match_port.py` + `business/match/start_match_adapter.py` (UC013 — Iniciar Partida): valida ator monitor (via `require_monitor` no controller), partida em SCHEDULED, ambos os times APPROVED, os dois times já definidos na partida (não permite iniciar partida ainda TBD/BYE) e a regra de 1 partida IN_PROGRESS por monitor. Ao iniciar: `status = IN_PROGRESS`, `started_at = now()`, `clock_seconds = 0`, `clock_running = true`, `current_period = 1`, placares zerados, `monitor_id` preenchido, e cria o `MatchEvent` `MATCH_STARTED`.
- **Resposta rica no endpoint de início:** como essa resposta já seria necessária para a interface de gerenciamento em tempo real (Bloco de Dados 1 do UC013) e não há débito futuro planejado para "enriquecer" depois, o endpoint `POST /api/match/{match_id}/start` já devolve tudo de uma vez — times (com placar), lista de jogadores de cada time, configuração da modalidade (períodos, duração, tipo de pontuação) e a timeline com o evento `MATCH_STARTED` — em vez de só a `Match` crua. Esse mesmo formato de resposta (`MatchManagementResponse`) foi reaproveitado em todos os endpoints do UC014.
- Testes unitários em `tests/unit/business/match/test_start_match_adapter.py` (6 testes): início bem-sucedido, bloqueio por status diferente de SCHEDULED, bloqueio por time não aprovado, bloqueio por times ainda não definidos, bloqueio por monitor já gerenciando outra partida, e o caso de borda em que a partida "em andamento" encontrada é a própria partida sendo iniciada (não deve bloquear).
- **UC014 — Registrar Evento — CONCLUÍDO** (`core/business/match/{register_goal,register_card,pause_clock,resume_clock,start_period,end_period,end_set}_port.py` + adapters correspondentes em `business/match/`, compartilhando validações comuns em `business/match/_shared.py`):
  - **Gol/Ponto** (`register_goal_adapter`): valida partida IN_PROGRESS e monitor responsável, time e jogador pertencentes à partida, bloqueia jogador `EXPELLED` (Fluxo Alternativo 7), incrementa o placar do time e cria o evento `GOAL` ou `POINT` (conforme `ScoreType` da modalidade) com `clock_seconds` calculado a partir do cronômetro autoritativo (ADR 0001).
  - **Cartão** (`register_card_adapter`): cartão amarelo conta cartões amarelos anteriores do jogador **nesta partida**; no 2º amarelo gera automaticamente um evento `EXPULSION` (`triggered_by: "second_yellow"`, `auto_generated: true`); vermelho direto gera `EXPULSION` imediata (`triggered_by: "direct_red"`); bloqueia registrar cartão para jogador já expulso.
  - **Cronômetro** (`pause_clock_adapter`, `resume_clock_adapter`): alternam `clock_running` reaproveitando o snapshot autoritativo do ADR 0001 (sem persistir tick a tick).
  - **Período** (`end_period_adapter`, `start_period_adapter`): `end_period` pausa o cronômetro e cria `PERIOD_END`; `start_period` incrementa `current_period`, retoma o cronômetro e cria `PERIOD_START` — dois endpoints/eventos separados, monitor decide quando avançar (RN 29-33).
  - **Set de vôlei** (`end_set_adapter`): implementa a normalização definida no [ADR 0002](../adr/ADR002_NormalizacaoModalidade.md) — persiste cada set em uma tabela própria (`MatchSet`/`match_set_repository`) em vez de um blob JSON, valida 25 pontos com diferença de 2 (ou os pontos do "final set" configurados por modalidade quando é o set decisivo), usa `lock_for_update` na partida para evitar condição de corrida ao concluir o set, incrementa `sets_won` do time vencedor e zera o placar do set atual. **Nota:** o próprio ADR 0002 ainda está com `Status: Proposta (ainda não implementada)` — o texto do ADR ficou desatualizado em relação ao código e deveria ser corrigido em paralelo a este plano.
  - `web/controllers/match_controller.py`: `POST /api/match/{match_id}/goal`, `/card`, `/clock/pause`, `/clock/resume`, `/period/end`, `/period/start`, `/set/end` — todos atrás de `require_monitor` e devolvendo `MatchManagementResponse`.
  - Testes unitários em `tests/unit/business/match/` (27 testes novos, 33 no total do módulo `match`): `test_register_goal_adapter.py` (7), `test_register_card_adapter.py` (4, incluindo 2º amarelo e vermelho direto), `test_clock_adapters.py` (4), `test_period_adapters.py` (3), `test_end_set_adapter.py` (9, incluindo set normal, set decisivo e a fila de condição de corrida via lock). Suíte completa (`pytest tests/unit/business/match/`) passando: 33/33.
  - **Débito técnico introduzido nesta rodada (não documentado em TODO no código — deveria ser adicionado):** nenhum dos sete adapters do UC014 chama o `AuditLogger` nem existe valor correspondente no enum `AuditAction` (`domain/enums/audit_action.py` só tem `MATCH_STARTED`, herdado do UC013). Isso quebra a RN41-42 e o item correspondente dos Critérios de Aceitação do UC014 ("o sistema deve registrar todas as operações para auditoria"), apesar da infraestrutura de auditoria já existir e estar em uso em `season`, `team`, `bracket` e `start_match_adapter`.
  - **Débito técnico assumido (mesmo padrão das fases anteriores):** WebSocket/SSE (canais `/matches/{match_id}/live` e `/seasons/{season_id}/live`) e Push Notification para alunos dependem da infraestrutura da Fase 6 — a decisão de transporte (SSE, ver ADR 0003) já foi tomada, mas a implementação ainda não começou; nenhum dos sete endpoints do UC014 publica em canal algum hoje.
- **UC015 — Finalizar Partida — CONCLUÍDO**, entregue em duas rodadas por causa do volume de regras de negócio:
  - **Decisões tomadas no início da rodada (registradas na conversa, não em ADR, por serem específicas deste UC):**
    1. **Estratégia de avanço automático no chaveamento:** com persistência (em vez de recalcular a posição a partir do sorteio a cada finalização) — mais robusta e rastreável, e resolve a observação em aberto desde a Fase 4.
    2. **Débito técnico de auditoria do UC014** (os sete adapters sem `AuditLogger`, RN41-42): deixado para uma rodada separada, dedicada só a isso — o UC015 registra apenas a própria auditoria, sem tentar fechar o débito alheio.
    3. **Disputa de pênaltis (Fluxo Alternativo 1):** implementado o fluxo completo, cobrança-a-cobrança, com casos de uso e endpoints próprios (`start_penalty_shootout`, `register_penalty_kick`, `end_penalty_shootout`) e eventos `PENALTY_GOAL`/`PENALTY_MISS` na timeline — em vez de um único endpoint recebendo o placar de pênaltis já pronto.
  - **Patch 1 — avanço automático no chaveamento + fluxo principal (sem pênaltis):**
    - Coluna `next_match_id` (FK auto-referenciada em `matches`, nullable) calculada no momento do sorteio: `business/bracket/engine/draw_engine.py` ganhou `MatchSpec.next_match_index` (índice, dentro da lista de partidas do `DrawPlan`, da partida da rodada seguinte que recebe o vencedor), calculado em `build_knockout_tree` para toda a árvore de mata-mata (inclusive BYE, por consistência, embora BYEs nunca passem por `finish_match`). `create_bracket_adapter` e `resort_bracket_adapter` foram refatorados para usar um novo helper compartilhado, `business/bracket/_shared.py::persist_draw_matches`, que gera os IDs no lado da aplicação e resolve `next_match_id` em uma única passada de `save`.
    - `core/business/match/finish_match_port.py` + `business/match/finish_match_adapter.py` (endpoint `POST /api/match/{match_id}/finish`): valida partida IN_PROGRESS e monitor responsável, determina o vencedor pelo placar, finaliza (`status = FINISHED`, `finished_at`, cronômetro pausado) e cria o evento `MATCH_END`.
    - Lógica de finalização extraída para `business/match/_finish_shared.py` (`finalize_match` e funções auxiliares), justamente para ser reaproveitada pelo fluxo de pênaltis do Patch 2 sem duplicação — depois de decidido o vencedor (por placar ou por pênaltis), o restante do processo é idêntico.
    - Avanço de vencedor em KNOCKOUT via `next_match_id` (`advance_knockout_winner`, com `lock_for_update` na partida de destino para evitar condição de corrida quando duas partidas irmãs terminam ao mesmo tempo); avanço do perdedor de SEMIFINAL para o 3º lugar localizado por `match_type` dentro do bracket (RN30 do UC — não por posição), via novo método `MatchRepositoryPort.find_by_bracket_and_type`.
    - Empate em GROUP finaliza normalmente com `winner_id = NULL` e atualiza a classificação (`BracketGroupTeam`: pontos, vitórias/empates/derrotas, saldo de gols) dos dois times.
    - Empate em KNOCKOUT **é bloqueado** (`ensure_knockout_tie_requires_penalties`) — o endpoint `/finish` recusa com uma mensagem orientando a iniciar a disputa de pênaltis; só o Patch 2 resolve esse caminho.
  - **Patch 2 — disputa de pênaltis (Fluxo Alternativo 1):**
    - Campos novos em `Match`: `penalty_shootout_active` (bool) e `team1_penalty_score`/`team2_penalty_score` (contadores separados do placar oficial — RN19/20/23: pênaltis nunca alteram `team1_score`/`team2_score`).
    - Três casos de uso/endpoints próprios: `start_penalty_shootout` (valida empate + KNOCKOUT, zera os contadores), `register_penalty_kick` (`team_id` + `result` GOAL/MISS, `player_id` opcional — a interface de pênaltis do UC não exige seleção de jogador; incrementa o contador se convertido e cria o evento `PENALTY_GOAL`/`PENALTY_MISS` na timeline) e `end_penalty_shootout` (monta o `penalty_result` — `{"team1_penalties", "team2_penalties", "winner_id"}` — e delega para `finalize_match`, o mesmo usado pelo Patch 1).
    - Novos enums: `EventType.PENALTY_GOAL`/`PENALTY_MISS`, `AuditAction.PENALTY_SHOOTOUT_STARTED`, `PenaltyKickResult` (GOAL/MISS).
  - `web/controllers/match_controller.py` ampliado com `POST /api/match/{match_id}/finish`, `/penalty-shootout/start`, `/penalty-shootout/kick` e `/penalty-shootout/end`, todos atrás de `require_monitor` e devolvendo `MatchManagementResponse` (agora também com `winner_id`, `penalty_result`, `penalty_shootout_active` e `penalty_score` por time).
  - Migrations `08134248a8f8_v10` (`next_match_id`) e `3fbd6f2e9a41_v11` (`penalty_shootout_active`, `team1_penalty_score`, `team2_penalty_score`), ambas encadeadas no head da árvore do Alembic.
  - Testes unitários novos em `tests/unit/business/match/` e `tests/unit/business/bracket/`: `test_finish_match_adapter.py` (8), `test_penalty_shootout_adapters.py` (12), `test_persist_draw_matches.py` (1) e extensão de `test_draw_engine.py` com `TestNextMatchIndexLinking` (4) cobrindo o encadeamento de `next_match_index` (potência de 2, BYE, `GROUP_STAGE_KNOCKOUT` com offset). Suíte completa (`pytest tests/unit/`) passando: 224/224.
  - **Débito técnico assumido (mesmo padrão das fases anteriores):** WebSocket/SSE e Push Notification para o `/finish` e os três endpoints de pênaltis dependem da Fase 6, assim como no UC014 — RN7 e os critérios de aceitação correspondentes do UC015 seguem pendentes até lá.
- **Pendente nesta fase:** UC017 (Corrigir Evento) e o débito técnico de auditoria do UC014 (item 7 da lista de próximos passos, adiado conscientemente na rodada do UC015) — ficam para as próximas rodadas.
- Também não implementado até aqui (fora do escopo de UC013/UC014/UC015): endpoints de consulta de partida (`GET /api/match/{match_id}`, listagens por temporada/time) — mesmo padrão de débito técnico já assumido para os `GET`s de chaveamento na Fase 4.

### Fase 6 — Tempo real (UC016)
- Hoje não há nenhuma infraestrutura de tempo real implementada, mas a decisão de transporte já foi tomada no [ADR 0003](../adr/ADR003_EnvioDeEventos.md) (ainda em `Status: Proposta`): **SSE** em vez de WebSocket, com reconciliação por `GET` de estado completo a cada reconexão. Falta implementar:
  - Os dois canais SSE previstos pelo ADR: `GET /api/seasons/{season_id}/live` e `GET /api/matches/{match_id}/live` (`StreamingResponse`/`sse-starlette`), com broadcaster em memória (fila por conexão) na primeira versão.
  - Publicação nas filas a partir dos adapters da Fase 5 — hoje nenhum dos adapters do UC013/UC014 publica em canal algum; será necessário instrumentá-los (`score_update`, `goal_scored`/`point_scored`, `card_issued`, `player_expelled`, `clock_update`, `period_ended`/`period_started`, `set_finished` etc.).
  - Push Notifications (mencionadas nos documentos) — definir provedor (FCM/APNs) e camada de integração (`core/notifications/`, ainda inexistente).
- Esta fase depende funcionalmente da Fase 5 estar concluída (os eventos precisam existir antes de serem transmitidos) — UC013/UC014/UC015 já geram eventos (incluindo `MATCH_END`, `PENALTY_GOAL`/`PENALTY_MISS`); falta apenas UC017 para o conjunto completo do Bloco de Dados 4 do UC016.

### Fase 7 — Gestão de Reportes (UC018)
Único caso de uso sem nenhuma camada implementada — precisa ser construído do zero, seguindo o mesmo padrão das demais entidades:
- `domain/report.py` + enum de status (`PENDING`, e os status futuros mencionados no documento) + enum de categoria da denúncia.
- `persistence/model/report_entity.py`, mapper, adapter, `core/persistence/report_repository_port.py`.
- `core/business/report/create_report_port.py` + adapter (denúncia anônima vs identificada, vínculo à temporada ativa).
- `web/controllers/report_controller.py`.
- Testes.

### Fase 8 — Transversal (pode/deve ser feito em paralelo às fases acima)
- **Testes:** `tests/unit` já existe e cobre `season`/`modality`; falta ampliar para `team`/`users`, além de estruturar `tests/integration` (banco sqlite em memória via `aiosqlite`, já presente nas deps de dev) e `tests/e2e`. Ativar `task coverage` no CI.
- **CI:** não há indício de pipeline de CI no repositório — configurar GitHub Actions rodando `task lint` e `task test` a cada PR, para que quebras de build como a corrigida na Fase 0 sejam pegas automaticamente.
- **`user_controller.py`:** já implementado e registrado em `main.py` (endpoints de administração de usuário) — item concluído, removido do backlog.
- **Documentação técnica:** `README.md` está vazio — vale documentar como rodar o projeto localmente (setup `uv`, variáveis de ambiente, docker-compose).

---

## 4. Ordem recomendada de execução (resumo)

```
Fase 0 (destravar build)  →  ✅ concluída
Fase 1 (Temporadas)       →  ✅ concluída  →  Fase 2 (Modalidades)  →  ✅ concluída
        ↓
Fase 3 (Equipes, UC006-008)  →  ✅ concluída
        ↓
Fase 4 (Chaveamento, UC011-012)  →  ✅ concluída  →  Fase 5 (Partidas, UC013 ✅ / UC014 ✅ / UC015 ✅ / UC017 pendente)  →  Fase 6 (Tempo real)
        ↓ (paralelo, independente)
Fase 7 (Reportes)
        ↓ (contínuo, do início ao fim)
Fase 8 (Testes/CI/Docs)
```

## 5. Próximos passos imediatos
1. ~~Abrir uma PR só com a Fase 0 (fix do build)~~ — concluído.
2. ~~Implementar UC001, UC002 e UC003 (Fase 1)~~ — concluído nesta revisão do plano.
3. ~~Priorizar a Fase 3 (UC006, UC007, UC008) para fechar por completo a Gestão de Equipes~~ — concluído: ciclo de inscrição de time ponta a ponta (criar → entrar via convite → gerenciar membros → submeter → aprovar → confirmar doação) está funcional.
4. ~~Priorizar a Fase 4 (UC011, UC012 — Chaveamento), já que Chaveamento e Partida dependem de um ciclo de equipes completo, agora disponível~~ — concluído: criação de chaveamento (sorteio, BYE, grupos, mata-mata, transição automática da temporada) e gestão (re-sorteio, edição e deleção de partidas) funcionais ponta a ponta.
5. ~~Priorizar a Fase 5 (UC013-015, UC017 — Partidas). Antes de iniciar, definir com o time a estratégia de rastreamento da árvore do chaveamento (ver observação registrada na Fase 4) para viabilizar o avanço automático de vencedores.~~ — UC013 (Iniciar Partida) concluído: coluna `monitor_id` criada em `matches` para rastrear qual monitor gerencia qual partida; endpoint de início funcional com resposta rica (times, jogadores, configuração da modalidade). A estratégia de avanço automático no chaveamento (`next_match_id` ou equivalente) segue em aberto para o UC015.
6. ~~Priorizar UC014 (Registrar Evento) como próximo passo da Fase 5 — depende do que já foi entregue no UC013 (partida IN_PROGRESS, cronômetro e monitor_id). Antes de implementar o controle de cronômetro, seguir a decisão registrada no [ADR 0001](../adr/ADR001_Cronometro.md).~~ — concluído: gol/ponto, cartão (com expulsão automática no 2º amarelo e no vermelho direto), pausar/retomar cronômetro, encerrar/iniciar período e encerrar set de vôlei (seguindo a normalização proposta no [ADR 0002](../adr/ADR002_NormalizacaoModalidade.md)) funcionais ponta a ponta, com 33 testes unitários em `tests/unit/business/match/`.
7. Fechar o débito técnico introduzido pelo UC014: adicionar chamadas ao `AuditLogger` (e os valores correspondentes em `AuditAction`) nos sete adapters de `business/match/` que hoje não registram auditoria (gol, cartão, pausar/retomar cronômetro, período, set) — ver observação na Fase 5. **Adiado conscientemente uma segunda vez:** na rodada do UC015 foi decidido, junto com o time, manter esse item separado (o UC015 registra apenas a própria auditoria) para não misturar o débito de um UC com a implementação do outro. Segue pendente, agora como próximo passo depois do UC017. Também vale atualizar o `Status` do [ADR 0002](../adr/ADR002_NormalizacaoModalidade.md) para refletir que a normalização já foi implementada.
8. ~~Priorizar UC015 (Finalizar Partida) como próximo passo da Fase 5 — é o caso de uso que efetivamente precisa da estratégia de avanço automático no chaveamento (`next_match_id` ou equivalente), ainda em aberto desde a observação registrada ao final da Fase 4.~~ — concluído em duas rodadas: **patch 1** (coluna `next_match_id` calculada no sorteio e persistida em `create_bracket_adapter`/`resort_bracket_adapter`; `finish_match_adapter` com avanço automático de vencedor em KNOCKOUT, avanço de perdedor de semifinal para 3º lugar por `match_type`, atualização de classificação em GROUP, endpoint `POST /api/match/{match_id}/finish`) e **patch 2** (disputa de pênaltis completa — `start_penalty_shootout`, `register_penalty_kick`, `end_penalty_shootout` como casos de uso e endpoints separados, com timeline de eventos `PENALTY_GOAL`/`PENALTY_MISS`). 20 testes unitários novos (`test_finish_match_adapter.py`, `test_penalty_shootout_adapters.py`, `test_persist_draw_matches.py`, extensão de `test_draw_engine.py`); suíte completa em 224/224.
9. Fechar a Fase 5 com UC017 (Corrigir Evento) — único caso de uso restante da fase.
10. Depois de UC017: (a) fechar o débito técnico de auditoria do UC014 (item 7, adiado duas vezes); (b) seguir para as Fases 6–7 na ordem já prevista, mantendo a Fase 8 (testes/CI/docs) em paralelo contínuo — incluindo a dívida de testes unitários de UC005 a UC010 registrada na Fase 3 e os `GET`s de chaveamento e de partida registrados como débito técnico nas Fases 4 e 5.