# Plano de Execução — Intercurso IFRN Backend

> Baseado na leitura dos 18 casos de uso em `docs/` e na análise do código-fonte atual do repositório `SIXBRO-CORPORATION/intercurso-ifrn-backend` (branch `main`).
>
> **Atualizado em 2026-07-06** após a conclusão da Fase 3 (UC006, UC007 e UC008). O diagnóstico e a tabela abaixo refletem o estado real do código nesta data, não mais o estado descrito nas versões anteriores deste plano.

---

## 1. Diagnóstico do estado atual

O projeto segue uma arquitetura em camadas (hexagonal/ports & adapters): `domain` → `core` (ports/interfaces) → `business` (adapters/casos de uso) → `persistence` (SQLAlchemy) → `web` (FastAPI). O padrão de caso de uso usa `Command`/`Context` (`core/command.py`, `core/context.py`).

**O build está destravado.** A Fase 0 foi concluída: `core/business/team/` e `business/team/` foram implementados (`create_team_port/adapter`, `approve_team_port/adapter`, `confirm_donation_port/adapter`), a aplicação sobe sem `ImportError` e a pasta `tests/` existe e está em uso.

**Padrão geral encontrado (revisado):**
- **Domain + Persistence (models, mappers, adapters, ports):** construídos para praticamente todas as entidades do sistema (Season, Modality, Team, Bracket, Match, etc.) — trabalho de infraestrutura bem avançado.
- **Business (casos de uso reais):** implementado para Autenticação, Usuário (criar/buscar/atualizar perfil), **Temporada (UC001, UC002 e UC003 completos)**, **Modalidade (UC004 completo)** e **Equipe (UC005 a UC010 completos)**. Chaveamento e Partida seguem sem lógica de negócio.
- **Web (controllers/rotas):** `auth_controller`, `user_controller`, `season_controller` e `modality_controller` funcionais e registrados em `main.py`. `team_controller` completo para o ciclo de vida do time: criar, entrar via convite, selecionar capitão, remover membro, sair do time, submeter para aprovação, aprovar e confirmar doação.
- **Testes:** `tests/unit/business` existe e cobre os adapters de `season` e `modality` (via mocks das ports). Ainda não há testes de `tests/integration` nem `tests/e2e`, e a cobertura de `team`/`users` é incompleta.
- **Jobs automáticos (UC001/UC002):** implementados via APScheduler (`scheduling/configuration/scheduler.py` + `scheduling/jobs/season_scheduler_jobs.py`), rodando a cada 1 minuto para abrir/fechar inscrições automaticamente.
- **UC018 (Reportar Jogador):** não existe absolutamente nada — nem domínio, nem persistência, nem enum de status.
- **UC016 (Visualizar Partida em Tempo Real):** nenhuma infraestrutura de WebSocket no projeto (nenhuma ocorrência de `websocket` no código).

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
| 011 | Criar Chaveamento | ✅ | ✅ | ❌ | ❌ |
| 012 | Gerenciar Chaveamento | ✅ | ✅ | ❌ | ❌ |
| 013 | Iniciar Partida | ✅ | ✅ | ❌ | ❌ |
| 014 | Registrar Evento | ✅ | ✅ | ❌ | ❌ |
| 015 | Finalizar Partida | ✅ | ✅ | ❌ | ❌ |
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

### Fase 4 — Gestão de Chaveamento (UC011, UC012)
- `core/business/bracket/create_bracket_port` (sorteio de times, geração de partidas, transição automática da temporada para IN_PROGRESS na primeira criação) e `manage_bracket_port` (re-sortear, editar/deletar partidas).
- Algoritmo de geração de chaveamento (mata-mata e fase de grupos) é a peça de maior complexidade dessa fase — vale um design/spike antes de codar.
- `web/controllers/bracket_controller.py`.
- Testes, com atenção especial ao algoritmo de sorteio/geração de partidas.

### Fase 5 — Gestão de Partidas (UC013, UC014, UC015, UC017)
- `core/business/match/start_match_port`, `register_event_port` (gol/ponto, cartões, expulsão, controle de cronômetro, períodos/sets), `finish_match_port` (definição de vencedor, avanço automático no chaveamento, pênaltis), `correct_event_port` (desfazer/deletar evento, soft delete, recalcular placar).
- Essa é a fase com mais regras de negócio por documento (UC014 e UC015 têm ~20KB cada) — recomenda-se quebrar em múltiplos PRs pequenos por fluxo alternativo.
- `web/controllers/match_controller.py`.
- Testes unitários fortes em cálculo de placar, avanço de chaveamento e regras de pênaltis/empate.

### Fase 6 — Tempo real (UC016)
- Hoje não há nenhuma infraestrutura de WebSocket. É necessário decidir e implementar:
  - Canal FastAPI WebSocket (`/seasons/{season_id}/live`, canal por partida).
  - Broadcast dos eventos gerados nas Fases 5 (`score_update`, `goal_scored`, `event_deleted` etc.).
  - Push Notifications (mencionadas nos documentos) — definir provedor (FCM/APNs) e camada de integração (`core/notifications/`).
- Esta fase depende funcionalmente da Fase 5 estar concluída (os eventos precisam existir antes de serem transmitidos).

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
Fase 4 (Chaveamento)  →  próxima prioridade  →  Fase 5 (Partidas)  →  Fase 6 (Tempo real)
        ↓ (paralelo, independente)
Fase 7 (Reportes)
        ↓ (contínuo, do início ao fim)
Fase 8 (Testes/CI/Docs)
```

## 5. Próximos passos imediatos
1. ~~Abrir uma PR só com a Fase 0 (fix do build)~~ — concluído.
2. ~~Implementar UC001, UC002 e UC003 (Fase 1)~~ — concluído nesta revisão do plano.
3. ~~Priorizar a Fase 3 (UC006, UC007, UC008) para fechar por completo a Gestão de Equipes~~ — concluído: ciclo de inscrição de time ponta a ponta (criar → entrar via convite → gerenciar membros → submeter → aprovar → confirmar doação) está funcional.
4. Priorizar a Fase 4 (UC011, UC012 — Chaveamento), já que Chaveamento e Partida dependem de um ciclo de equipes completo, agora disponível.
5. Validar com o time se o mecanismo de agendamento de jobs (já resolvido na Fase 1 com APScheduler) atende também às necessidades futuras da Fase 4, e se a estratégia de WebSocket/Push (Fase 6) já foi decidida em alguma ADR/discussão não presente no repo.
6. Depois da Fase 4, seguir para Fases 5–7 na ordem já prevista, mantendo a Fase 8 (testes/CI/docs) em paralelo contínuo — incluindo a dívida de testes unitários de UC005 a UC010 registrada na Fase 3.