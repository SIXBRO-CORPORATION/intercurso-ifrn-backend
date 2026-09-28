from datetime import UTC, datetime, timedelta
from typing import Callable, Optional
from uuid import UUID
import jwt

from core.realtime.live_ticket_port import InvalidLiveTicketError, LiveTicketPort
from security.config import settings

DEFAULT_TICKET_TTL_SECONDS = 30
TICKET_SCOPE_CLAIM = "live_ticket"
ANONYMOUS_SUBJECT = "anonymous"


class LiveTicketAdapter(LiveTicketPort):

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TICKET_TTL_SECONDS,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._secret_key = settings.live_ticket_secret_key
        self._algorithm = settings.jwt_algorithm
        self._ttl_seconds = ttl_seconds
        self._clock = clock

    def issue_ticket(self, user_id: Optional[UUID], channel: str) -> str:
        now = self._clock()
        payload = {
            "sub": str(user_id) if user_id is not None else ANONYMOUS_SUBJECT,
            "scope": TICKET_SCOPE_CLAIM,
            "channel": channel,
            "iat": now,
            "exp": now + timedelta(seconds=self._ttl_seconds),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_ticket(self, ticket: str, channel: str) -> Optional[UUID]:
        try:
            payload = jwt.decode(
                ticket,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidLiveTicketError(f"Ticket inválido: {exc}") from exc

        if payload.get("scope") != TICKET_SCOPE_CLAIM:
            raise InvalidLiveTicketError("Token informado não é um ticket de tempo real")

        if payload.get("channel") != channel:
            raise InvalidLiveTicketError("Ticket não é válido para o canal solicitado")

        sub = payload.get("sub")
        if sub == ANONYMOUS_SUBJECT:
            return None

        try:
            return UUID(sub)
        except (TypeError, ValueError) as exc:
            raise InvalidLiveTicketError("Ticket sem usuário válido") from exc