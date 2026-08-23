from core.command import Command
from domain.season.season import Season


class GetActiveSeasonPort(Command[Season]):
    """UC005 - Gestão de Equipes: consulta da temporada ativa no momento.

    Não espera nenhuma propriedade no Context.

    Retorna a Season marcada como ativa (`active = true`). Lança
    BusinessException se não houver nenhuma temporada ativa no momento.
    """

    pass
