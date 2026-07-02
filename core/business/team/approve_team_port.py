from core.command import Command
from domain.team import Team


class ApproveTeamPort(Command[Team]):
    """UC009 - Aprovar Equipes.

    Espera no Context:
        - property "team_id": UUID do time a ser aprovado
        - property "approved_by_user_id": UUID do monitor que está aprovando
    """

    pass
