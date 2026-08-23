from core.command import Command
from domain.team.team import Team


class GetTeamDetailsPort(Command[Team]):
    """UC008/UC009 - Visualizar detalhes de um time e seus membros.

    Espera no Context (properties):
        - "team_id": UUID do time (obrigatório)
        - "requesting_user_id": UUID do usuário autenticado (obrigatório)
        - "requesting_user_role": UserRole do usuário autenticado
          (obrigatório)

    Preenche no Context (properties):
        - "modality": Modality vinculada ao time
        - "members": List[TeamMember] membros do time
        - "member_users_by_id": Dict[UUID, User] com os usuários dos membros
        - "owner_user": User dono do time
        - "captain_user": Optional[User] capitão do time, se selecionado

    Regras:
        - Monitor/Admin podem visualizar qualquer time;
        - Demais usuários só podem visualizar times dos quais são membros.

    Retorna o Team encontrado. Lança BusinessException se o time não
    existir ou se o usuário não tiver permissão para visualizá-lo.
    """

    pass
