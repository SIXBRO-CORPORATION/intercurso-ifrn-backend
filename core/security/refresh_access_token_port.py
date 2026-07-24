from core.command import Command
from domain.security.auth_token import AuthToken


class RefreshAccessTokenPort(Command[AuthToken]):
    pass
