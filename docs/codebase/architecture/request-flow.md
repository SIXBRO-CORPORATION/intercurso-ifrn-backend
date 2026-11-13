# Fluxo de uma requisição

1. Controller (`web/controllers/*_controller.py`) recebe o request, resolve dependências (`Depends(get_<caso>_port)`, `require_authenticated_user` ou `require_monitor`).
2. Controller preenche o `Context`: `context.put_property("team_id", ...)`.
3. `await port.execute(context)` chama o adapter de `business/`.
4. Adapter lê com `context.get_property("team_id", UUID)`, usa repositórios (ports), chama `audit_logger.log(...)` em ações relevantes, devolve o resultado (dados extras podem voltar pelo `context`).
5. Mapper de `web/mappers/` converte domínio -> response; controller devolve `ApiResponse[...]`.
6. Exceções de domínio viram `ApiResponse` em `web/commons/exception_handler.py`. Mensagens ao usuário em português.

Injeção: providers `get_<caso>_port` em `web/dependencies/business/<dominio>_dependencies.py`, reexportados em `web/dependencies/__init__.py`.
