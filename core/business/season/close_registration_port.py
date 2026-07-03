from core.command import Command
from domain.season import Season


class CloseRegistrationPort(Command[Season]):
    """UC002 - Gerenciar Temporada: Encerrar Inscrições Antecipadamente
    (Fluxo Alternativo 3).

    Espera no Context (properties):
        - "season_id": UUID da temporada
        - "closed_by": UUID do monitor responsável

    Regras de negócio aplicadas pelo adapter (ver docs/UC002):
        - apenas temporadas em REGISTRATION_OPEN podem ser encerradas
          antecipadamente;
        - status muda para REGISTRATION_CLOSED imediatamente;
        - registration_closed_at = now().
    """

    pass
