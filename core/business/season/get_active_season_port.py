from core.command import Command
from domain.season.season import Season


class GetActiveSeasonPort(Command[Season]):
    """UC005 - Gestão de Equipes: consulta da temporada ativa no momento.

    Não espera nenhuma propriedade no Context.

    Retorna a Season marcada como ativa (`active = true`). Se não houver
    nenhuma ativa (intervalo entre a finalização de uma temporada e a
    criação da próxima), retorna a última temporada criada. Lança
    NotFoundException apenas se nunca houve temporada.
    """

    pass
