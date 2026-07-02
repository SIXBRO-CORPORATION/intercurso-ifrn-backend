# Plano de Execução — Intercurso IFRN Backend

> Baseado na leitura dos 18 casos de uso em `docs/` e na análise do código-fonte atual do repositório `SIXBRO-CORPORATION/intercurso-ifrn-backend` (branch `main`).

---

## 1. Diagnóstico do estado atual

O projeto segue uma arquitetura em camadas (hexagonal/ports & adapters): `domain` → `core` (ports/interfaces) → `business` (adapters/casos de uso) → `persistence` (SQLAlchemy) → `web` (FastAPI). O padrão de caso de uso usa `Command`/`Context` (`core/command.py`, `core/context.py`).

**Achado crítico: a aplicação não sobe.** `web/main.py` inclui `team_router`, que importa `core.business.team.approve_team_port`, `create_team_port`, `confirm_donation_port` — módulos que **não existem no repositório**. `web/dependencies/business/team_dependencies.py` também referencia `business.team.create_team_adapter`, `approve_team_adapter` etc., igualmente inexistentes. Confirmei isso executando o import (`ModuleNotFoundError: No module named 'core.business.team'`). Ou seja, o histórico do git mostra que a última grande entrega (PR "feature/new-entities") criou domínio + persistência para todas as entidades, mas a camada de negócio de Equipes ficou pela metade e quebrou o boot da aplicação.

**Padrão geral encontrado:**
- **Domain + Persistence (models, mappers, adapters, ports):** construídos para praticamente todas as entidades do sistema (Season, Modality, Team, Bracket, Match, etc.) — trabalho de infraestrutura bem avançado.
- **Business (casos de uso reais):** existe apenas para Autenticação (login SUAP, refresh token) e Usuário (criar/buscar perfil). Para Temporada, Modalidade, Equipe, Chaveamento e Partida, a lógica de negócio **não existe**, exceto os 3 casos quebrados de Equipe.
- **Web (controllers/rotas):** só há `auth_controller` (funcional) e `team_controller` (quebrado). `user_controller` existe mas está vazio e nem é registrado em `main.py`.
- **Testes:** `pyproject.toml` e `pytest.ini` configuram `tests/unit`, `tests/integration`, `tests/e2e`, mas **a pasta `tests/` não existe** no repositório.
- **UC018 (Reportar Jogador):** não existe absolutamente nada — nem domínio, nem persistência, nem enum de status.
- **UC016 (Visualizar Partida em Tempo Real):** nenhuma infraestrutura de WebSocket no projeto (nenhuma ocorrência de `websocket` no código).

### Tabela: Casos de uso × estado das camadas

| UC | Caso de uso | Domain | Persistence | Business | Web/API |
|----|---|:---:|:---:|:---:|:---:|
| 001 | Criar Temporada | ✅ | ✅ | ❌ | ❌ |
| 002 | Gerenciar Temporada | ✅ | ✅ | ❌ | ❌ |
| 003 | Finalizar Temporada | ✅ | ✅ | ❌ | ❌ |
| 004 | Cadastrar Modalidade | ✅ | ✅ | ❌ | ❌ |
| 005 | Criar Equipe | ✅ | ✅ | ⚠️ referenciado, ausente | ⚠️ quebrado (import) |
| 006 | Entrar via Convite | ✅ | ✅ | ❌ | ❌ |
| 007 | Gerenciar Membros | ✅ | ✅ | ❌ | ❌ |
| 008 | Submeter Equipe | ✅ | ✅ | ❌ | ❌ |
| 009 | Aprovar Equipe | ✅ | ✅ | ⚠️ referenciado, ausente | ⚠️ quebrado (import) |
| 010 | Confirmar Doação | ✅ | ✅ | ⚠️ referenciado, ausente | ⚠️ quebrado (import) |
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

1. **Nada pode ser entregue antes de destravar o build.** Prioridade zero absoluta.
2. Implementar a camada `business` seguindo rigorosamente o padrão já estabelecido (`Command[R]` + `Context`, ports em `core/business/<módulo>/*_port.py`, adapters em `business/<módulo>/*_adapter.py`), reaproveitando o que já existe em `core/persistence` e `domain`.
3. Seguir a ordem de dependência funcional entre os casos de uso (Temporada → Modalidade → Equipe → Chaveamento → Partida → Tempo real → Reportes), que é também a ordem sugerida pela numeração dos próprios documentos em `docs/`.
4. Criar a pasta `tests/` desde a Fase 0, com pelo menos testes unitários por caso de uso à medida que ele é implementado (o projeto já está configurado para isso, só falta o conteúdo).

---

## 3. Fases de execução

### Fase 0 — Destravar o build (bloqueador, prioridade máxima)
- Criar `core/business/team/` com os ports que faltam: `create_team_port.py`, `create_team_members_port.py`, `approve_team_port.py`, `confirm_donation_port.py`.
- Criar `business/team/` com os adapters correspondentes: `create_team_adapter.py`, `create_team_members_adapter.py`, `approve_team_adapter.py`, `confirm_donation_adapter.py`, implementando as regras já descritas em UC005, UC009 e UC010.
- Rodar `uv run uvicorn web.main:app` (ou equivalente) e confirmar que a aplicação sobe sem `ImportError`.
- Criar `tests/unit`, `tests/integration`, `tests/e2e` (mesmo que vazios com `__init__.py`) para que `task test` pare de falhar.
- **Critério de aceite:** app sobe, `/health` responde, `task test` executa (mesmo que sem testes ainda).

### Fase 1 — Gestão de Temporadas (UC001, UC002, UC003)
- `core/business/season/`: `create_season_port`, `manage_season_port` (editar datas, encerrar antecipadamente), `finish_season_port`.
- `business/season/`: adapters implementando as regras de negócio de cada UC (transições DRAFT → REGISTRATION_OPEN → REGISTRATION_CLOSED → IN_PROGRESS → FINISHED, validação de nome de confirmação em UC003, desativação de convites de time ao finalizar).
- Job/agendamento automático de abertura/encerramento de inscrições (UC001 menciona "jobs automáticos") — decidir mecanismo (ex.: APScheduler, Celery beat, ou verificação no request) já que não há infraestrutura de agendamento no projeto hoje.
- `web/controllers/season_controller.py` + request/response models + mapper, seguindo o padrão de `team_controller.py`.
- Testes unitários dos adapters + testes de integração das rotas.

### Fase 2 — Gestão de Modalidades (UC004)
- `core/business/modality/create_modality_port.py` + adapter, com validações: nome duplicado, `min_members` ≥ 1, `max_members` ≥ `min_members`.
- `web/controllers/modality_controller.py`.
- Testes.

### Fase 3 — Completar Gestão de Equipes (UC005–UC010)
Já com UC005/009/010 destravados na Fase 0, falta:
- UC006 — Entrar via Convite: `join_team_via_invite_port/adapter` (validação de token, temporada ativa, aluno não estar em outro time da modalidade).
- UC007 — Gerenciar Membros: `select_captain_port`, `remove_member_port`, `leave_team_port`.
- UC008 — Submeter Equipe: `submit_team_port` (validação de mínimo de membros, transição para PENDING_APPROVAL).
- Ampliar `team_controller.py` com as novas rotas e os respectivos modelos de request/response.
- Testes cobrindo os fluxos alternativos descritos nos documentos (nome duplicado, limites inválidos, confirmação incorreta etc.).

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
- **Testes:** estruturar `tests/unit` (mocks das ports), `tests/integration` (banco sqlite em memória via `aiosqlite`, já presente nas deps de dev) e `tests/e2e`. Ativar `task coverage` no CI.
- **CI:** não há indício de pipeline de CI no repositório — configurar GitHub Actions rodando `task lint` e `task test` a cada PR, para que quebras de build como a da Fase 0 sejam pegas automaticamente.
- **`user_controller.py`:** hoje vazio e não registrado — decidir se será usado (ex.: endpoint de perfil, listagem para monitor) ou removido.
- **Documentação técnica:** `README.md` está vazio — vale documentar como rodar o projeto localmente (setup `uv`, variáveis de ambiente, docker-compose).

---

## 4. Ordem recomendada de execução (resumo)

```
Fase 0 (destravar build)  →  bloqueador, fazer primeiro e sozinho
Fase 1 (Temporadas)       →  Fase 2 (Modalidades)  →  Fase 3 (Equipes, completar)
        ↓
Fase 4 (Chaveamento)  →  Fase 5 (Partidas)  →  Fase 6 (Tempo real)
        ↓ (paralelo, independente)
Fase 7 (Reportes)
        ↓ (contínuo, do início ao fim)
Fase 8 (Testes/CI/Docs)
```

## 5. Próximos passos imediatos
1. Abrir uma PR só com a Fase 0 (fix do build) — é pequena, urgente e desbloqueia qualquer outro trabalho em paralelo.
2. Validar com o time se o mecanismo de agendamento de jobs (Fase 1) e a estratégia de WebSocket/Push (Fase 6) já foram decididos em alguma ADR/discussão não presente no repo — são as duas decisões de infraestrutura com maior impacto arquitetural do backlog.
3. Priorizar Fases 1–3 antes de 4–7, já que sem Temporada/Modalidade/Equipe funcionando não há dados para testar Chaveamento e Partidas.