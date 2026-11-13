# Adicionar um caso de uso

1. Leia o UC em `docs/planning/spec/UC0xx_*.md` (fonte de verdade das regras).
2. Port em `core/business/<dominio>/<caso>_port.py`; adapter em `business/<dominio>/<caso>_adapter.py`.
3. Provider `get_<caso>_port` em `web/dependencies/business/<dominio>_dependencies.py` e export em `web/dependencies/__init__.py`.
4. Rota no controller: `ApiResponse[...]`, `Depends(require_authenticated_user)` ou `require_monitor`. Router novo: registre em `web/main.py`.
5. Request/response em `web/models/`, mapper em `web/mappers/`.
6. Teste unitário em `tests/unit/business/<dominio>/`.
7. Auditoria (`audit_logger.log`) se a ação for relevante.
8. Atualize `docs/planning/ai/planejamento.md` se mudar o estado de um UC.
