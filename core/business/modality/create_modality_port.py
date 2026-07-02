from core.command import Command
from domain.modality import Modality


class CreateModalityPort(Command[Modality]):
    """UC004 - Cadastrar Modalidade.

    Espera no Context:
        - data: Modality (name, min_members, max_members preenchidos)

    Regras de negócio aplicadas pelo adapter:
        - nome não pode ser vazio e deve ser único no sistema;
        - min_members >= 1;
        - max_members >= min_members;
        - modalidade é sempre criada com active=True.
    """

    pass
