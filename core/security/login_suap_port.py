from core.command import Command
from domain.auth_token import AuthToken


class LoginWithSUAPPort(Command[AuthToken]):
    """
    Port (interface) para o caso de uso de login com SUAP

    Define o contrato que LoginWithSUAPAdapter deve implementar.
    """
    pass