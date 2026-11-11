# CLAUDE.md

Backend FastAPI do Intercurso IFRN (temporadas, modalidades, equipes, chaveamento, partidas, SSE).
Visão geral, variáveis de ambiente e Docker estão no `README.md`; não repita aqui.

## Comandos

Use `uv run task <nome>` (taskipy, definido em `pyproject.toml`):

- `run` sobe a API com reload (`web.main:app`, porta 8000)
- `test`, `test_unit`, `test_integration`, `test_e2e` rodam o pytest
- `lint` roda `ruff check .`; `check` roda lint e testes (o CI faz o mesmo em `pr-verify.yml`)
- Teste isolado: `uv run pytest tests/unit/business/team/test_approve_team_adapter.py -k nome`
- Migrations: `uv run alembic upgrade head`; nova: `uv run alembic revision --autogenerate -m "descricao"`

Python 3.12. Ambiente de desenvolvimento no Windows (PowerShell).

## Arquitetura (hexagonal: ports & adapters)

Dependências apontam para dentro: `web` -> `core` (ports) <- `business`/`persistence`/`security`/`messaging`/`storage`.

- `domain/`: entidades, enums e exceções. Sem dependência de framework.
- `core/`: apenas contratos (ports) e utilitários compartilhados (`Command`, `Context`, `realtime/`).
  - `core/business/<dominio>/<caso>_port.py`: um port por caso de uso.
  - `core/persistence/<dominio>/*_repository_port.py`: ports de repositório.
- `business/<dominio>/<caso>_adapter.py`: implementação do caso de uso. Helpers compartilhados do módulo ficam em `_shared.py`.
- `persistence/`: `model/` (entidades SQLAlchemy), `mappers/` (entidade <-> domínio), `adapters/` (repositórios).
- `web/`: `controllers/`, `models/request|response/`, `mappers/` (domínio -> response), `dependencies/` (injeção).
- `security/`, `messaging/` (FCM/push, notifiers), `storage/` (R2), `scheduling/` (APScheduler, iniciado no `lifespan` de `web/main.py`).

### Padrão de caso de uso

- Port: `class XPort(Command[R])` e nada mais. Adapter: `class XAdapter(XPort)` com `async def execute(self, context: Context) -> R`.
- Entrada e saídas auxiliares trafegam pelo `Context`: o controller faz `context.put_property("team_id", ...)`, o adapter lê com `context.get_property("team_id", UUID)` e pode devolver dados extras pelo mesmo `context`.
- O adapter recebe ports (repositórios, `AuditLogger`, notifiers) no `__init__`. Nunca importe `persistence` direto em `business`.
- Erros de negócio: `BusinessException` (400), `ConflictException` (409), `NotFoundException` (404), de `domain/exceptions/`. O `web/commons/exception_handler.py` os converte em `ApiResponse`. Mensagens ao usuário são em português.
- Ações relevantes chamam `audit_logger.log(...)`.

### Para adicionar um caso de uso

1. Port em `core/business/<dominio>/`, adapter em `business/<dominio>/`.
2. Provider `get_<caso>_port` em `web/dependencies/business/<dominio>_dependencies.py` (e exporte em `web/dependencies/__init__.py`, que os controllers importam).
3. Rota no controller, usando `ApiResponse[...]`, `Depends(require_authenticated_user)` ou `require_monitor`.
4. Se for um router novo, registre-o em `web/main.py`.
5. Teste unitário espelhando o caminho em `tests/unit/business/<dominio>/`.
6. Mudou o schema? Gere a migration Alembic (`alembic/versions/`).

## Testes

- `tests/unit` espelha a estrutura do código; repositórios e ports são `AsyncMock`, o adapter é construído manualmente (veja `make_adapter()` em `test_approve_team_adapter.py`).
- Marque com `@pytest.mark.unit` (ou `integration`/`e2e`/`slow`): `--strict-markers` está ligado. `asyncio_mode = auto`, então não precisa de `@pytest.mark.asyncio`.
- O `conftest.py` da raiz define as variáveis de ambiente falsas; os testes não precisam de `.env` nem de banco.

## Regras e cuidados

- A fonte de verdade das regras de negócio é `docs/spec/UC0xx_*.md`; decisões de arquitetura estão em `docs/adr/`. Consulte o UC correspondente antes de mudar o comportamento de um caso de uso.
- Modelo de acesso: leitura pública, ação autenticada (ADR004). Ao criar rota de leitura, decida conscientemente entre pública e restrita a monitor.
- O cronômetro de partida é sempre calculado no servidor (ADR001). O broadcaster SSE é em memória por processo (ADR003); não assuma múltiplos workers.
- Nunca versione segredos: `.env*` (exceto `*.example`) e `credentials/` estão fora do git.
- O README documenta `compose.dev.yml` e `compose.prod.yml`; `docker-compose*.yml` na raiz são arquivos paralelos, então confirme antes de editá-los.
