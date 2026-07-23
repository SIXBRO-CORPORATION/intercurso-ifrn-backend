from core.command import Command
from domain.season.season import Season


class GetSeasonDetailsPort(Command[Season]):
    """UC002 - Gerenciar Temporada: Fluxo Principal (Visualizar Temporada).

    Espera no Context (properties):
        - "season_id": UUID da temporada

    Preenche no Context (properties):
        - "season_modalities": List[SeasonModality] vinculadas à temporada
        - "total_teams_created": int
        - "total_teams_submitted": int
        - "total_teams_approved": int
        - "available_actions": List[str] ações de workflow disponíveis
          para o status atual da temporada

    Retorna a Season encontrada. Lança BusinessException se não existir.
    """

    pass
