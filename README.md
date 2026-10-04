# Intercurso IFRN — Backend

Backend do sistema de gestão do **Intercurso IFRN**: cadastro e gerenciamento de temporadas,
modalidades esportivas, equipes, chaveamento (brackets) e partidas, com autenticação via SUAP
(OAuth2) e atualizações em tempo real (SSE) para acompanhamento de jogos.

## Stack

- **Python 3.12+**
- **FastAPI** — API HTTP
- **SQLAlchemy 2.0 (async)** + **asyncpg** — acesso a dados
- **Alembic** — migrations
- **PostgreSQL 17**
- **APScheduler** — jobs agendados
- **PyJWT** — autenticação JWT
- **SUAP OAuth2** — login institucional
- **uv** + **taskipy** — gerenciamento de ambiente e tasks
- **pytest** — testes (unitários, integração, e2e)
- **ruff** — lint

## Arquitetura

O projeto segue uma organização em camadas, aproximando-se de uma arquitetura hexagonal
(ports & adapters):

```
web/          → controllers, models de request/response, dependências HTTP (camada de entrada)
business/     → casos de uso / adapters de negócio, organizados por domínio (bracket, match,
                modality, season, team, users)
core/         → ports (contratos) e regras de negócio compartilhadas
domain/       → entidades de domínio e enums
persistence/  → mappers, models de banco e adapters de repositório
security/     → autenticação, JWT, integração OAuth2 com o SUAP
scheduling/   → jobs agendados (APScheduler)
alembic/      → migrations do banco de dados
docs/         → especificações de casos de uso (docs/spec), ADRs (docs/adr) e planejamento
tests/        → tests/unit, tests/integration, tests/e2e
```

Cada módulo de negócio (`business/*`) expõe *adapters* que implementam os casos de uso descritos
em `docs/spec`, seguindo as regras de negócio documentadas ali.

## Principais funcionalidades

- **Autenticação institucional** via OAuth2 do SUAP, com emissão de JWT e refresh token
- **Gestão de temporadas** (criar, gerenciar, encerrar, reabrir inscrições)
- **Gestão de modalidades esportivas**
- **Gestão de equipes** (criação, convites, membros, capitão, aprovação, confirmação de doação)
- **Gestão de chaveamento** (criação e reorganização de brackets, sugestão automática de
  configuração)
- **Gestão de partidas** (início, registro e correção de eventos, cronômetro, finalização)
- **Acompanhamento público** de partidas sem login (lista paginada, detalhe e feed ao vivo)
- **Agendamento de jobs** para rotinas automáticas do sistema (ex.: transições de estado de
  temporada/partida)

## Modelo de acesso

Regra geral: **leitura pública, ação autenticada** ([ADR 0004](docs/adr/ADR004_ModeloDeAcesso.md)).
Qualquer pessoa abre o app e acompanha o Intercurso sem login; o login só é pedido quando a
pessoa tenta uma ação que depende de identidade (criar equipe, denunciar, gerir partidas).

| Capacidade | Visitante | Aluno | Monitor |
|---|:-:|:-:|:-:|
| Ver temporada ativa, modalidades, partidas, placar, cronômetro e eventos | ✔ | ✔ | ✔ |
| Feed ao vivo (SSE de temporada e de partida) | ✔ | ✔ | ✔ |
| Ver nome de jogadores/times em partidas | ✔ | ✔ | ✔ |
| Ver matrícula de jogadores | ✘ | ✘ | Só em telas de gestão |
| Detalhe de equipe com membros e convites | ✘ | Só a própria | ✔ |
| Criar/gerir equipe, aceitar convite, submeter | ✘ | ✔ | ✔ |
| Denunciar (UC018) e receber push | ✘ | ✔ | — |
| Gestão de temporada, modalidade, chaveamento, partida | ✘ | ✘ | ✔ |

Rotas públicas de leitura hoje: `GET /api/season/active`, `GET /api/modality/`,
`GET /api/match/` (paginada, com filtros), `GET /api/match/{id}` e os canais SSE. Classificação,
chaveamento e lista de temporadas ainda são restritos a monitor. Detalhes em
[Estado de implementação](docs/adr/ADR004_ModeloDeAcesso.md#estado-de-implementação).

## Comunicação em tempo real

O acompanhamento ao vivo usa **Server-Sent Events (SSE)** com broadcaster em memória por processo
([ADR 0003](docs/adr/ADR003_EnvioDeEventos.md)). O cronômetro é sempre calculado no servidor
([ADR 0001](docs/adr/ADR001_Cronometro.md)).

1. O cliente pede um ticket de 30 s em `POST /api/realtime/ticket` (com ou sem login; visitantes
   têm limite de taxa por IP).
2. Conecta em `GET /api/season/{id}/live?ticket=...` (feed) ou
   `GET /api/match/{id}/live?ticket=...` (detalhe; só partidas `IN_PROGRESS`).
3. Ao reconectar, sincroniza o estado com `GET /api/match/{id}` (schema público).

Conexões SSE são limitadas por usuário e por IP. Push notifications (UC016, Fluxo Alternativo 2)
ainda não estão implementadas.

## Como rodar o projeto

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker (para o PostgreSQL) ou uma instância própria do PostgreSQL

### 1. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

Variáveis relevantes:

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/db_name
DATABASE_URL_SYNC=postgresql://username:password@localhost:5432/db_name
SUAP_CLIENT_ID=suap_client_id
SUAP_CLIENT_SECRET=suap_client_secret
SUAP_REDIRECT_URI=http://localhost:8000/api/auth/callback
JWT_SECRET_KEY=strong_key
LIVE_TICKET_SECRET_KEY=outro_valor_diferente_do_jwt
FRONTEND_URL=http://localhost:5173

MOBILE_DEEP_LINK_SCHEME=myapp
MOBILE_DEEP_LINK_PATH=callback
```

### 2. Subir o banco de dados

```bash
docker compose up -d
```

### 3. Instalar dependências

```bash
uv venv
uv pip install .
uv pip install --group dev
```

Ou, usando as tasks já definidas no projeto:

```bash
uv run task install
```

### 4. Rodar as migrations

```bash
uv run alembic upgrade head
```

### 5. Rodar a aplicação

```bash
uv run task run
```

A API sobe em `http://localhost:8000`, com documentação interativa em `/docs` (Swagger) e
`/redoc`.

## Tasks disponíveis (taskipy)

```bash
uv run task install          # cria venv e instala dependências (prod + dev)
uv run task run               # sobe a aplicação com reload
uv run task test              # roda todos os testes
uv run task test_unit         # roda apenas testes unitários
uv run task test_integration  # roda apenas testes de integração
uv run task test_e2e          # roda apenas testes e2e
uv run task coverage          # roda testes com relatório de cobertura
uv run task lint              # roda o ruff
uv run task check             # lint + testes
uv run task clean             # remove artefatos de build/cache
```

## Rotas da API

Prefixo base `/api`, com os seguintes recursos:

| Prefixo | Recurso |
|---|---|
| `/api/auth` | Autenticação (login SUAP, refresh, logout) |
| `/api/user` | Usuários |
| `/api/season` | Temporadas |
| `/api/modality` | Modalidades esportivas |
| `/api/team` | Equipes |
| `/api/bracket` | Chaveamento |
| `/api/match` | Partidas |

Além disso:

- `GET /health` — health check da aplicação e do banco de dados

A lista completa e detalhada de endpoints, parâmetros e schemas está disponível em `/docs`
(Swagger UI) com o servidor em execução.

## Testes

```bash
uv run task test              # todos os testes
uv run task test_unit          # apenas unitários
uv run task test_integration   # apenas integração
uv run task test_e2e           # apenas e2e
uv run task coverage           # com cobertura (core, domain, business, auth, persistence)
```

## Documentação

- [`docs/spec`](docs/spec) — especificações de casos de uso (UC001–UC018), com regras de negócio
  detalhadas
- [`docs/adr`](docs/adr) — Architecture Decision Records
- [`docs/ai/planejamento.md`](docs/ai/planejamento.md) — planejamento do projeto

## Docker

Uma imagem de produção pode ser construída a partir do `Dockerfile` incluso, que instala as
dependências com `uv`, aplica as migrations e sobe a aplicação com `uvicorn`:

```bash
docker build -t intercurso-ifrn-backend .
docker run --env-file .env -p 8000:8000 intercurso-ifrn-backend
```
