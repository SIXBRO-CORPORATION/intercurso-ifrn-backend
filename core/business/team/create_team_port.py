from core.command import Command
from domain.team import Team


class CreateTeamPort(Command[Team]):
    """UC005 - Criar Equipe.

    Espera no Context:
        - data: Team (name, photo, modality_id preenchidos)
        - property "creator_user_id": UUID do aluno que está criando o time

    Preenche no Context:
        - property "owner_member": TeamMember do owner recém-criado
    """

    pass
