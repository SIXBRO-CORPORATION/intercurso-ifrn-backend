from typing import List

from core.command import Command
from domain.team.team import Team


class ListTeamsPort(Command[List[Team]]):
    """UC005/UC009 - Listagem de times.

    Espera no Context (properties):
        - "requesting_user_id": UUID do usuário autenticado (obrigatório)
        - "requesting_user_role": UserRole do usuário autenticado (obrigatório)
        - "status": TeamStatus para filtrar (opcional, apenas monitor/admin)
        - "season_id": UUID da temporada para filtrar (opcional, apenas
          monitor/admin)

    Preenche no Context (properties):
        - "team_extra_info": Dict[UUID, dict] com informações agregadas por
          time (modality_name, owner_name, members_count,
          donations_confirmed, donations_total), usadas para montar a
          resposta resumida.

    Regras:
        - Alunos (role USER) sempre recebem apenas os próprios times
          (times dos quais são membros), independentemente dos filtros
          informados;
        - Monitor/Admin podem listar todos os times, filtrando por status
          e/ou temporada (UC009 - Listar Times Pendentes).

    Retorna a lista de Team encontrada.
    """

    pass
