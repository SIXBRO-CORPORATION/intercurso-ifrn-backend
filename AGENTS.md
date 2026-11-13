# AGENTS.md: Intercurso IFRN Backend

Briefing para agentes de IA. Leia este arquivo, depois **só** o documento indicado para a tarefa.

## 1. Briefing
Backend FastAPI do Intercurso IFRN: temporadas, modalidades, equipes, chaveamento, partidas ao vivo (SSE), notificações push. Login via SUAP (OAuth2) + JWT. Arquitetura hexagonal (ports & adapters). Python 3.12, SQLAlchemy async, PostgreSQL, Alembic, uv + taskipy, pytest, ruff.
Visão geral e Docker: `README.md`. Resumo operacional: `CLAUDE.md`.

Idioma: identificadores e commits em inglês (`feat(match): ...`); mensagens ao usuário, docs e comentários em português-BR.

## Comandos
`uv run task <nome>`: `run` (API, porta 8000), `test`, `test_unit`, `test_integration`, `test_e2e`, `lint`, `check` (lint + testes, igual ao CI). Teste isolado: `uv run pytest tests/unit/business/team/test_approve_team_adapter.py -k nome`. Migrations: `uv run alembic upgrade head`.

## 2. Regras duras
1. `business/` nunca importa `persistence/`; dependa de ports em `core/`.
2. Um port por caso de uso: `XPort(Command[R])`; adapter `XAdapter` com `execute(self, context)`.
3. Entrada pelo `Context` (`put_property`/`get_property`); injeção via `web/dependencies/`.
4. Erros de negócio só com `BusinessException`/`ConflictException`/`NotFoundException`; mensagem em português.
5. Ação relevante chama `audit_logger.log(...)`.
6. Rota de leitura: decidir pública vs. monitor (ADR004). Gestão exige `require_monitor`.
7. Cronômetro calculado no servidor (ADR001); broadcaster SSE é em memória, sem multi-worker (ADR003).
8. Mudou comportamento: leia o `docs/planning/spec/UC0xx` antes; mudou schema: migration Alembic.
9. Nunca versione segredos (`.env*` exceto `*.example`, `credentials/`).
10. Teste unitário espelhando o caminho em `tests/unit/`, com `@pytest.mark.unit` (sem `@pytest.mark.asyncio`); repositórios e ports como `AsyncMock`, adapter montado à mão (`make_adapter()`); sem banco nem `.env`.
11. Nunca commitar em `main`/`develop`. Antes de entregar: `uv run task check`.
12. Mudou algo descrito em `docs/`: atualize o documento no mesmo PR.

## 3. Armadilhas
| Armadilha | Efeito |
|---|---|
| Esquecer export em `web/dependencies/__init__.py` | Controller não importa o provider |
| Router novo fora de `web/main.py` | Rota não existe |
| `docker-compose*.yml` da raiz | Paralelos aos `compose.*.yml` oficiais; confirmar antes de editar |
| Marcador de teste ausente/inválido | `--strict-markers` quebra a suíte |
| Adapters do UC014 sem `AuditLogger` | Débito conhecido (RN41-42), ver `docs/planning/ai/planejamento.md` |
| Ambiente do dev é Windows/PowerShell | Cuidado com caminhos e scripts shell |

## 4. Mapa da documentação
`AGENTS.md -> docs/codebase/README.md -> docs/codebase/<categoria>/README.md -> documento`

| Tarefa | Leia |
|---|---|
| Entender camadas / onde criar arquivo | `docs/codebase/architecture/layers.md` |
| Seguir o caminho de uma requisição | `docs/codebase/architecture/request-flow.md` |
| SSE, ticket, jobs, push | `docs/codebase/architecture/realtime-and-jobs.md` |
| Novo caso de uso / endpoint | `docs/codebase/guides/add-use-case.md` |
| Mudança de schema | `docs/codebase/guides/add-migration.md` |
| Nomes, erros, auditoria | `docs/codebase/conventions/code.md` |
| Escrever teste | `docs/codebase/conventions/testing.md` |
| Branch, commit, CI | `docs/codebase/conventions/git.md` |
| Biblioteca disponível | `docs/codebase/stack/README.md` |
| Modelo de acesso, UCs, ADRs | `docs/codebase/domain/README.md` |
| Comandos, variáveis de ambiente | `docs/codebase/reference/README.md` |
| Regra de negócio de um caso | `docs/planning/spec/UC0xx_*.md` |
| Decisão de arquitetura | `docs/planning/adr/ADR00x_*.md` |
| Estado de implementação por UC | `docs/planning/ai/planejamento.md` |

## 5. Mapa do código
```
web/          controllers, models request/response, mappers, dependencies, main.py
core/         ports (business/, persistence/), command.py, context.py, realtime/
business/     adapters por domínio: bracket, match, modality, season, team, users, messaging
domain/       entidades, enums, exceptions
persistence/  model/, mappers/, adapters/, database.py
security/ messaging/ storage/ scheduling/ seeds/ alembic/
tests/        unit (espelha o código), integration, e2e
```

## 6. Protocolo
1. Localize pelos índices; não varra a árvore.
2. Veja se já existe helper (`_shared.py` do módulo) antes de criar.
3. Siga o arquivo vizinho (padrão local vence).
4. Rode `uv run task check`; relate a saída real.
5. Atualize a documentação afetada.

Se uma instrução do usuário conflitar com uma regra daqui, aponte em uma frase e siga o usuário.
