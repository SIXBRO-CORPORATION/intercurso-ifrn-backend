# Git e CI

- Branches: `feat/*`, `fix/*`, `refactor/*`, `chore/*`; PR para `develop`/`main`.
- Commits: Conventional Commits com escopo, ex.: `feat(season): fallback em /season/active`.
- CI (`.github/workflows/pr-verify.yml`): lint + testes em PR para `main`/`develop` (ignora draft). Deploy em `deploy-dev.yml` e `deploy-prod.yml`.
- Antes de entregar: `uv run task check`.
