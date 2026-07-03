from core.command import Command
from domain.season import Season


class ManageSeasonPort(Command[Season]):
    """UC002 - Gerenciar Temporada: Editar Datas de Inscrição.

    Cobre os Fluxos Alternativos 1 (editar abertura/encerramento em DRAFT),
    2 (editar apenas encerramento em REGISTRATION_OPEN) e 5 (adiar
    abertura em DRAFT) — as três são, na prática, a mesma operação de
    atualização de datas com regras diferentes conforme o status atual.

    Espera no Context (properties):
        - "season_id": UUID da temporada a ser editada
        - "new_registration_start_date": Optional[datetime] (apenas DRAFT)
        - "new_registration_end_date": Optional[datetime]
        - "reason": Optional[str] motivo da alteração (auditoria)
        - "updated_by": UUID do monitor responsável

    Regras de negócio aplicadas pelo adapter (ver docs/UC002):
        - só permite edição em status DRAFT ou REGISTRATION_OPEN;
        - em DRAFT: pode editar abertura e/ou encerramento;
        - em REGISTRATION_OPEN: só pode editar encerramento;
        - nova data de abertura deve ser >= agora;
        - nova data de encerramento deve ser > data de abertura efetiva.
    """

    pass
