# Migration

1. Alterar modelo em `persistence/model/`.
2. `uv run alembic revision --autogenerate -m "descricao"` (revisar o arquivo gerado em `alembic/versions/`).
3. `uv run alembic upgrade head`.
4. Ajustar mapper e adapter de repositório correspondentes.
