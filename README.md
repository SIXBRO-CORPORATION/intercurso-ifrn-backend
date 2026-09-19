# Intercurso IFRN — Backend

Backend do sistema de gestão do **Intercurso IFRN**: cadastro e gerenciamento de temporadas,
modalidades esportivas, equipes, chaveamento (brackets) e partidas, com autenticação via SUAP
(OAuth2) e suporte planejado a atualizações em tempo real para acompanhamento de jogos.

## Stack

- **Python 3.12+**
- **FastAPI** — API HTTP
- **SQLAlchemy 2.0 (async)** + **asyncpg** — acesso a dados
- **Alembic** — migrations
- **PostgreSQL 17**
- **APScheduler** — jobs agendados
- **PyJWT / python-jose** — autenticação JWT
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
- **Agendamento de jobs** para rotinas automáticas do sistema (ex.: transições de estado de
  temporada/partida)

## Comunicação em tempo real (em definição)

O acompanhamento de partidas ao vivo — placar, cronômetro e eventos como gols e cartões —
depende de algum mecanismo de **comunicação em tempo real** entre backend e clientes (app dos
alunos, telas de monitor). Hoje o backend expõe apenas a API REST tradicional; **nenhuma infra de
tempo real está implementada ainda**, e esta é uma decisão de arquitetura em aberto.

### Por que é necessário

Conforme [`docs/spec/UC016_InterfaceUsuário_VisualizarPartida.md`](docs/spec/UC016_InterfaceUsuário_VisualizarPartida.md),
o sistema precisa:

- Atualizar placar e cronômetro de partidas `IN_PROGRESS` para múltiplos clientes simultaneamente,
  sem que cada um precise ficar dando polling na API;
- Propagar eventos de partida (gol, cartão, expulsão, início/fim de período/partida) assim que
  são registrados, para quem estiver acompanhando aquela partida ou o feed geral de uma temporada;
- Notificar usuários que não estão com o app aberto no momento de eventos importantes (gol, cartão
  vermelho, início/fim de partida) — provavelmente via push notification, o que é um mecanismo
  separado da conexão em tempo real em si.

Já existe uma decisão tomada sobre **onde mora a fonte da verdade do tempo de jogo** (o cálculo do
cronômetro é sempre feito no servidor, nunca confiado ao cliente) — ver
[`docs/adr/ADR001_Cronometro.md`](docs/adr/ADR001_Cronometro.md). O que ainda não foi decidido é
**qual tecnologia/infra vai transportar essas atualizações até o cliente**.

### Pontos a decidir

- **Protocolo/mecanismo**: WebSocket, Server-Sent Events, polling curto, ou um serviço gerenciado
  de pub/sub (ex.: Redis Pub/Sub, um broker externo, etc.);
- **Escopo dos canais**: hoje a especificação sugere um agrupamento por temporada (feed geral) e
  outro por partida específica (detalhe), mas isso pode mudar dependendo da solução escolhida;
- **Escala**: quantas partidas simultâneas e quantos clientes conectados por partida o sistema
  precisa suportar, e se o backend (hoje um único processo FastAPI/uvicorn) aguenta manter essas
  conexões abertas ou se isso deveria ser delegado a outro componente;
- **Reconexão e consistência**: como um cliente que reconecta (ex.: reload de tela, app voltando
  do background) recupera o estado atual sem depender de ter recebido todos os eventos anteriores;
- **Push notifications**: se ficam acopladas à mesma infra de tempo real ou são tratadas como um
  serviço à parte (ex.: FCM/APNs disparado pelo backend nos mesmos pontos onde eventos são
  registrados).

Os documentos citados acima (`UC016` e `ADR001`) servem como ponto de partida — descrevem o
comportamento esperado do ponto de vista de produto e uma decisão já tomada sobre a fonte da
verdade do cronômetro — mas não fecham qual infra de tempo real deve ser usada. Essa é a decisão
em aberto.

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
SUAP_CLIENT_ID=suap_client_id
SUAP_CLIENT_SECRET=suap_client_secret
SUAP_REDIRECT_URI=http://localhost:8000/api/auth/callback
JWT_SECRET_KEY=strong_key

MOBILE_DEEP_LINK_SCHEME=myapp
MOBILE_DEEP_LINK_PATH=callback
```

### 2. Subir o banco de dados

```bash
docker compose -f compose.dev.yml up -d postgres
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

Dois ambientes independentes, cada um com seu Compose, seu volume do PostgreSQL e seu arquivo de variáveis.

| | Development | Production |
|---|---|---|
| Compose | `compose.dev.yml` | `compose.prod.yml` |
| Dockerfile | `Dockerfile.dev` | `Dockerfile` (multi-stage) |
| Variáveis | `.env.dev` | `.env.prod` |
| Código | bind mount + `uvicorn --reload` | copiado para a imagem, sem reload |
| Usuário | root | não-root (uid 1000) |
| PostgreSQL | porta `127.0.0.1:5432` | sem porta publicada |
| API | `http://localhost:8000` | interna; acesso via Nginx em HTTPS (`443`) |

Serviços: `nginx` (apenas em produção), `postgres` (17, com healthcheck e volume nomeado), `migrate` (executa `alembic upgrade head` uma única vez e encerra) e `api` (só inicia após o banco saudável e a migration concluída). A API acessa o banco por `postgres:5432` na rede padrão do Compose.

### Variáveis de ambiente

Copie os exemplos (PowerShell) e ajuste os valores. Os arquivos `.env.dev` e `.env.prod` estão no `.gitignore`; nunca versione segredos.

```powershell
Copy-Item .env.dev.example .env.dev
Copy-Item .env.prod.example .env.prod
```

`DATABASE_URL` (asyncpg) e `DATABASE_URL_SYNC` (psycopg2, usada pelo Alembic) devem apontar para o host `postgres` e usar as mesmas credenciais de `POSTGRES_USER` e `POSTGRES_PASSWORD`.

### Development

```bash
docker compose -f compose.dev.yml up --build
docker compose -f compose.dev.yml logs -f api
docker compose -f compose.dev.yml down
```

O código de `alembic`, `business`, `core`, `domain`, `persistence`, `scheduling`, `security` e `web` é montado no container e o Uvicorn reinicia ao salvar arquivos (polling ativado para funcionar em bind mounts no Windows). Alterou `pyproject.toml` ou `uv.lock`? Rode com `--build`.

### Production

```bash
docker compose -f compose.prod.yml up --build -d
docker compose -f compose.prod.yml logs -f api
docker compose -f compose.prod.yml down
```

Em produção o Nginx é o único ponto de entrada: `80` redireciona para `443` (HTTPS) e repassa para a API pela rede interna. Ele espera os certificados em `nginx/certs/fullchain.pem` e `nginx/certs/privkey.pem` (ignorados pelo Git). Sem eles, o Nginx não inicia.

Certificado para teste local (PowerShell):

```powershell
docker run --rm -v "${PWD}/nginx/certs:/certs" alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /certs/privkey.pem -out /certs/fullchain.pem -subj "/CN=localhost"
```

Em servidor real, gere um certificado válido (ex.: Let's Encrypt com `certbot certonly --standalone -d seu-dominio`) e copie `fullchain.pem` e `privkey.pem` para `nginx/certs/`. Ajuste `SUAP_REDIRECT_URI` em `.env.prod` para a URL `https://`.

### Persistência e migrations

- Os dados ficam nos volumes nomeados `postgres_data_dev` e `postgres_data_prod`. `down` preserva os dados; `down -v` apaga.
- As migrations existentes são aplicadas pelo serviço `migrate` (`alembic upgrade head`). Nenhuma migration é gerada automaticamente. Para criar uma nova: `docker compose -f compose.dev.yml run --rm api alembic revision --autogenerate -m "descricao"`.
- Atalhos: `task docker_dev`, `task docker_dev_down`, `task docker_prod`, `task docker_prod_down`.
