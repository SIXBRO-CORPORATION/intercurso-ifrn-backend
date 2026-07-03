from core.command import Command
from domain.season import Season


class ReopenRegistrationPort(Command[Season]):
    """UC002 - Gerenciar Temporada: Reabrir Inscrições em Emergência
    (Fluxo Alternativo 4).

    Espera no Context (properties):
        - "season_id": UUID da temporada
        - "new_registration_end_date": datetime, nova data de encerramento
        - "reopened_by": UUID do monitor responsável

    Regras de negócio aplicadas pelo adapter (ver docs/UC002):
        - apenas temporadas em REGISTRATION_CLOSED podem ser reabertas;
        - monitor deve definir nova data de encerramento (> agora e > data
          de abertura da temporada);
        - status volta para REGISTRATION_OPEN;
        - temporadas FINISHED nunca podem ser reabertas por este comando.
    """

    pass
