# Tempo real, jobs e push

- **SSE** (ADR003): canais `GET /api/season/{id}/live` e `GET /api/match/{id}/live`. Admissão por ticket (`POST /api/realtime/ticket`, visitante limitado por IP, secret `LIVE_TICKET_SECRET_KEY`). Código em `core/realtime/` (`broadcaster.py`, `ip_rate_limiter.py`, `live_ticket_port.py`, `sse.py`).
- O broadcaster é **em memória por processo**: não assuma múltiplos workers.
- Publicação a partir dos controllers de partida. `GET /api/match/{id}` serve de reconciliação após reconexão.
- **Cronômetro** (ADR001): sempre calculado no servidor.
- **Jobs**: `scheduling/configuration/scheduler.py` + `scheduling/jobs/season_scheduler_jobs.py`, a cada 1 min (abre/fecha inscrições).
- **Push** (ADR005): FCM em `messaging/`; `notification_controller.py`. Credenciais por `FIREBASE_CREDENTIALS_PATH` ou `_JSON`.
