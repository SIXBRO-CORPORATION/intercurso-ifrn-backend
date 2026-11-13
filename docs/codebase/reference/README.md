# Referência

## Comandos (`uv run task <nome>`)
| Task | Função |
|---|---|
| `run` | API com reload, porta 8000 (`web.main:app`) |
| `test` / `test_unit` / `test_integration` / `test_e2e` | pytest |
| `lint` | `ruff check .` |
| `check` | lint + testes (igual ao CI) |
| `coverage` | pytest com cobertura |
| `docker_dev` / `docker_prod` (+ `_down`) | compose dev/prod |

Migrations: `uv run alembic upgrade head`.

## Variáveis de ambiente (modelo em `.env.example`)
- Banco: `DATABASE_URL`, `DATABASE_URL_SYNC`
- SUAP: `SUAP_CLIENT_ID`, `SUAP_CLIENT_SECRET`, `SUAP_REDIRECT_URI_WEB`, `SUAP_REDIRECT_URI_MOBILE`
- Segredos: `JWT_SECRET_KEY`, `LIVE_TICKET_SECRET_KEY`
- Frontend/mobile: `FRONTEND_URL`, `MOBILE_DEEP_LINK_SCHEME`, `MOBILE_DEEP_LINK_PATH`
- R2: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_PRESIGNED_URL_EXPIRES_SECONDS`
- Firebase: `FIREBASE_CREDENTIALS_PATH`, `FIREBASE_CREDENTIALS_JSON`

Variantes: `.env.dev.example`, `.env.prod.example`.

## Compose
Oficiais: `compose.dev.yml`, `compose.prod.yml`. `docker-compose*.yml` na raiz são paralelos: confirmar antes de editar.
