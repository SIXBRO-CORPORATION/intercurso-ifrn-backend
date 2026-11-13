# Camadas (ports & adapters)

Dependências apontam para dentro:
`web` -> `core` (ports) <- `business` / `persistence` / `security` / `messaging` / `storage`.

| Pasta | Papel | Regra |
|---|---|---|
| `domain/` | Entidades, enums, exceções (`BusinessException` 400, `ConflictException` 409, `NotFoundException` 404) | Sem framework |
| `core/` | Contratos: `core/business/<dominio>/<caso>_port.py`, `core/persistence/<dominio>/*_repository_port.py`, `Command`, `Context`, `realtime/` | Só interfaces e utilitários |
| `business/<dominio>/` | Um `<caso>_adapter.py` por caso de uso; helpers do módulo em `_shared.py` | Nunca importa `persistence` |
| `persistence/` | `model/` (SQLAlchemy), `mappers/` (entidade <-> domínio), `adapters/` (repositórios), `database.py` | Implementa ports de `core/persistence` |
| `web/` | `controllers/`, `models/request\|response/`, `mappers/` (domínio -> response), `dependencies/` (injeção), `commons/` (`ApiResponse`, exception handler) | Só fala com ports |
| `security/` | JWT, OAuth2 SUAP | |
| `messaging/` | FCM, notifiers, conteúdo de notificações | |
| `storage/` | R2 (boto3, URL presignada) | |
| `scheduling/` | APScheduler, iniciado no `lifespan` de `web/main.py` | |
| `alembic/` | Migrations | |
| `seeds/` | `dev_seed.py` | |

Domínios de negócio: `bracket`, `match`, `modality`, `season`, `team`, `users`, `messaging`.
