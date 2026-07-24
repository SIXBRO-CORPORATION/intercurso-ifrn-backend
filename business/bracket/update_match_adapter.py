from datetime import datetime
from uuid import UUID

from core.business.bracket.update_match_port import UpdateMatchPort
from core.business.audit.audit_logger import AuditLogger
from core.context import Context
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.enums.match_status import MatchStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match


class UpdateMatchAdapter(UpdateMatchPort):
    def __init__(
        self,
        match_repository: MatchRepositoryPort,
        bracket_repository: BracketRepositoryPort,
        team_repository: TeamRepositoryPort,
        user_repository: UserRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.match_repository = match_repository
        self.bracket_repository = bracket_repository
        self.team_repository = team_repository
        self.user_repository = user_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Match:
        match_id = context.get_property("match_id", UUID)
        new_scheduled_date = context.get_property("scheduled_date", datetime)
        new_team1_id = context.get_property("team1_id", UUID)
        new_team2_id = context.get_property("team2_id", UUID)
        updated_by = context.get_property("updated_by", UUID)

        if match_id is None:
            raise BusinessException("Partida é obrigatória")

        if new_scheduled_date is None and new_team1_id is None and new_team2_id is None:
            raise BusinessException("Nenhum dado para atualização foi informado")

        match = await self.match_repository.get(match_id)
        if match is None:
            raise BusinessException("Partida não encontrada")

        if match.status != MatchStatus.SCHEDULED:
            raise BusinessException(
                "Somente partidas agendadas (SCHEDULED) podem ser editadas"
            )

        if new_team1_id is not None or new_team2_id is not None:
            bracket = await self.bracket_repository.get(match.bracket_id)
            if bracket is None:
                raise BusinessException("Chaveamento da partida não encontrado")

            for candidate_team_id in (new_team1_id, new_team2_id):
                if candidate_team_id is None:
                    continue

                candidate_team = await self.team_repository.get(candidate_team_id)
                if candidate_team is None:
                    raise BusinessException("Time informado não encontrado")

                if (
                    candidate_team.modality_id != bracket.modality_id
                    or candidate_team.season_id != bracket.season_id
                ):
                    raise BusinessException(
                        "O time informado não pertence à mesma modalidade/temporada "
                        "do chaveamento"
                    )

                if candidate_team.status != TeamStatus.APPROVED:
                    raise BusinessException(
                        "O time informado precisa estar com status APPROVED"
                    )

            if new_team1_id is not None:
                match.team1_id = new_team1_id
            if new_team2_id is not None:
                match.team2_id = new_team2_id

        if new_scheduled_date is not None:
            match.scheduled_date = new_scheduled_date

        saved_match = await self.match_repository.save(match)

        requesting_monitor = (
            await self.user_repository.get(updated_by) if updated_by else None
        )
        actor_role = (
            requesting_monitor.role.value
            if requesting_monitor is not None and requesting_monitor.role
            else None
        )
        changed_fields = [
            field_name
            for field_name, value in (
                ("data agendada", new_scheduled_date),
                ("time 1", new_team1_id),
                ("time 2", new_team2_id),
            )
            if value is not None
        ]
        await self.audit_logger.log(
            action=AuditAction.MATCH_UPDATED,
            description=(
                f"Partida atualizada ({', '.join(changed_fields)})"
            ),
            actor_id=updated_by,
            actor_role=actor_role,
        )

        return saved_match