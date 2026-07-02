from core.command import Command
from domain.team_member import TeamMember


class ConfirmDonationPort(Command[TeamMember]):
    """UC010 - Confirmar Doações.

    Espera no Context:
        - property "team_id": UUID do time
        - property "matricula": matrícula do membro a ter a doação confirmada
        - property "confirmed_by_user_id": UUID do monitor que está confirmando

    Preenche no Context:
        - property "user_updated": bool indicando se o vínculo do usuário foi
          atualizado (mantido por compatibilidade com o controller existente)
    """

    pass
