# Código

## Caso de uso
- Port: `class XPort(Command[R])` e nada mais, em `core/business/<dominio>/<caso>_port.py`.
- Adapter: `class XAdapter(XPort)` com `async def execute(self, context: Context) -> R`, em `business/<dominio>/<caso>_adapter.py`.
- Dependências (repositórios, `AuditLogger`, notifiers) entram pelo `__init__`, como ports.
- Entrada via `Context` (`put_property` / `get_property(nome, tipo)`).

## Regras
- `business` nunca importa `persistence`.
- Erros de negócio: exceções de `domain/exceptions/`; mensagem em português.
- Ação relevante chama `audit_logger.log(...)` (enum `domain/enums/audit_action.py`).
- Leitura pública vs. restrita a monitor: decidir conscientemente (ADR004).
- Nada de segredo versionado: `.env*` (exceto `*.example`) e `credentials/` fora do git.
- Lint: `ruff`. Python 3.12, async em todo o fluxo.

## Nomes
- Arquivos: `snake_case`; sufixos `_port.py`, `_adapter.py`, `_controller.py`, `_repository_port.py`.
- Identificadores e arquivos em inglês; mensagens de usuário em português.
