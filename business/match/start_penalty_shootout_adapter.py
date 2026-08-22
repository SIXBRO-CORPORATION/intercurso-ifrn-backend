from uuid import UUID

from business.match._finish_shared import ensure_penalty_shootout_can_start
from business.match._shared import load_management_context, validate_match_in_progress
from core.business.audit.audit_logger import AuditLogger
from core.business.match.start_penalty_shootout_port import StartPenaltyShootoutPort
from core.context import Context
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.match.match_set_repository_port import MatchSetRepositoryPort
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from core.persistence.modality.volleyball_modality_configuration_repository_port import \
    VolleyballModalityConfigurationRepositoryPort
from domain.enums.audit_action import AuditAction
from domain.match.match import Match


class StartPenaltyShootoutAdapter(StartPenaltyShootoutPort):

    def __init__(
        self,
        match_repository: MatchRepositoryPort,
        match_event_repository: MatchEventRepositoryPort,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        bracket_repository: BracketRepositoryPort,
        modality_repository: ModalityRepositoryPort,
        modality_configuration_repository: ModalityConfigurationRepositoryPort,
        volleyball_modality_configuration_repository: VolleyballModalityConfigurationRepositoryPort,
        match_set_repository: MatchSetRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.match_repository = match_repository
        self.match_event_repository = match_event_repository
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.bracket_repository = bracket_repository
        self.modality_repository = modality_repository
        self.modality_configuration_repository = modality_configuration_repository
        self.volleyball_modality_configuration_repository = (
            volleyball_modality_configuration_repository
        )
        self.match_set_repository = match_set_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Match:
        match_id = context.get_property("match_id", UUID)
        monitor_id = context.get_property("monitor_id", UUID)

        match = await validate_match_in_progress(
            self.match_repository, match_id, monitor_id
        )
        ensure_penalty_shootout_can_start(match)

        match.penalty_shootout_active = True
        match.team1_penalty_score = 0
        match.team2_penalty_score = 0

        saved_match = await self.match_repository.save(match)

        await self.audit_logger.log(
            action=AuditAction.PENALTY_SHOOTOUT_STARTED,
            description=(
                f"Disputa de pênaltis iniciada na partida {saved_match.id} "
                f"(empate {saved_match.team1_score}x{saved_match.team2_score} "
                "no tempo regulamentar)"
            ),
            actor_id=monitor_id,
        )

        await load_management_context(
            context,
            saved_match,
            self.team_repository,
            self.team_member_repository,
            self.user_repository,
            self.bracket_repository,
            self.modality_repository,
            self.modality_configuration_repository,
            self.match_event_repository,
            self.volleyball_modality_configuration_repository,
            self.match_set_repository,
        )

        return saved_match
