from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from core.realtime.live_ticket_port import InvalidLiveTicketError, LiveTicketPort
from security.config import settings

DEFAULT_TICKET_TTL_SECONDS = 300
TICKET_SCOPE_CLAIM = "live_ticket"


class LiveTicketAdapter(LiveTicketPort):

    def __init__(self, ttl_seconds: int = DEFAULT_TICKET_TTL_SECONDS) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._ttl_seconds = ttl_seconds

    def issue_ticket(self, user_id: UUID, channel: str) -> str:
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id),
            "scope": TICKET_SCOPE_CLAIM,
            "channel": channel,
            "iat": now,
            "exp": now + timedelta(seconds=self._ttl_seconds),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_ticket(self, ticket: str, channel: str) -> UUID:
        try:
            payload = jwt.decode(
                ticket,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"require": ["sub", "exp", "iat", "scope", "channel"]},
            )
        except JWTError as exc:
            raise InvalidLiveTicketError(f"Ticket inválido: {exc}") from exc

        if payload.get("scope") != TICKET_SCOPE_CLAIM:
            raise InvalidLiveTicketError("Token informado não é um ticket de tempo real")

        if payload.get("channel") != channel:
            raise InvalidLiveTicketError(
                "Ticket não é válido para o canal solicitado"
            )

        try:
            return UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise InvalidLiveTicketError("Ticket sem usuário válido") from exc
