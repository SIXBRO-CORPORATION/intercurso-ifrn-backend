from typing import List

from core.command import Command
from domain.season.season import Season


class ListSeasonsPort(Command[List[Season]]):
    """UC002 - Gerenciar Temporada: Fluxo Principal (Listagem de Temporadas).

    Espera no Context (properties, todas opcionais):
        - "status": SeasonStatus para filtrar temporadas por status
        - "year": int para filtrar temporadas por ano

    Retorna a lista de Season cadastradas, ordenadas por data de criação
    decrescente. Os filtros são mutuamente exclusivos; quando "status" é
    informado, "year" é ignorado.
    """

    pass
