# Testes

- `tests/unit` espelha o código: `tests/unit/business/<dominio>/test_<caso>_adapter.py`. `tests/integration` e `tests/e2e` existem, hoje vazios.
- Repositórios e ports são `AsyncMock`; o adapter é construído à mão (ver `make_adapter()` em `test_approve_team_adapter.py`).
- Marque com `@pytest.mark.unit` (ou `integration`/`e2e`/`slow`): `--strict-markers` ligado. `asyncio_mode = auto`: sem `@pytest.mark.asyncio`.
- `conftest.py` da raiz define variáveis de ambiente falsas: não precisa de `.env` nem de banco.
- Rodar um teste: `uv run pytest <caminho> -k nome`.
- Cobertura: `uv run task coverage`.
