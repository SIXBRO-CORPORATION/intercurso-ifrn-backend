from uuid import UUID

from core.business.bracket.delete_match_port import DeleteMatchPort
from core.context import Context
from core.persistence.match_repository_port import MatchRepositoryPort
from domain.enums.match_status import MatchStatus
from domain.exceptions.business_exception import BusinessException


class DeleteMatchAdapter(DeleteMatchPort):
    def __init__(self, match_repository: MatchRepositoryPort):
        self.match_repository = match_repository

    async def execute(self, context: Context) -> bool:
        match_id = context.get_property("match_id", UUID)
        if match_id is None:
            raise BusinessException("Partida é obrigatória")

        match = await self.match_repository.get(match_id)
        if match is None:
            raise BusinessException("Partida não encontrada")

        if match.status != MatchStatus.SCHEDULED:
            raise BusinessException(
                "Somente partidas agendadas (SCHEDULED) podem ser deletadas"
            )

        # TODO (débito técnico, mesmo padrão das fases anteriores): registro de
        # auditoria da deleção (monitor, partida, data/hora) depende de
        # infraestrutura ainda inexistente no projeto.

        deleted_count = await self.match_repository.delete(match_id)
        return deleted_count > 0
