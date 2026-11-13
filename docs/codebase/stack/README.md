# Stack

| Área | Tecnologia |
|---|---|
| Linguagem | Python >= 3.12 (`.python-version`) |
| API | FastAPI 0.115, uvicorn |
| Banco | PostgreSQL 17, SQLAlchemy 2.0 async + asyncpg; psycopg/psycopg2 para Alembic |
| Migrations | Alembic (+ alembic-utils) |
| Validação | Pydantic 2.10, pydantic-settings |
| Auth | SUAP OAuth2, PyJWT / python-jose |
| Jobs | APScheduler |
| Push | firebase-admin (FCM) |
| Storage | boto3 (Cloudflare R2) |
| HTTP client | httpx |
| Ambiente/tasks | uv + taskipy |
| Testes | pytest 9, pytest-asyncio, aiosqlite |
| Lint | ruff |
| Deploy | Docker (`compose.dev.yml`, `compose.prod.yml`), nginx |

Dependências em `pyproject.toml`; lockfile `uv.lock`. Não adicione biblioteca sem checar se uma já instalada resolve.
