from core.command import Command
from domain.season import Season


class CreateSeasonPort(Command[Season]):
    """UC001 - Criar Temporada.

    Espera no Context:
        - data: Season (name, year, registration_start_date,
          registration_end_date, rules_document preenchidos)
        - property "modality_ids": List[UUID] das modalidades vinculadas
        - property "open_immediately": bool (opcional, default False)
        - property "created_by": UUID do monitor responsável

    Preenche no Context:
        - property "season_modalities": List[SeasonModality] criadas

    Regras de negócio aplicadas pelo adapter (ver docs/UC001):
        - nome obrigatório; ano >= ano atual;
        - ao menos uma modalidade, todas existentes e ativas;
        - data de abertura >= agora (exceto abertura imediata);
        - data de encerramento > data de abertura;
        - status inicial DRAFT, exceto abertura imediata (REGISTRATION_OPEN);
        - apenas uma temporada pode estar active=True por vez.
    """

    pass
