from core.command import Command
from domain.auth_token import AuthToken


class RefreshAccessTokenPort(Command[AuthToken]):
    pass
