from core.command import Command
from domain.security.auth_token import AuthToken


class LoginWithSuapPort(Command[AuthToken]):
    pass
