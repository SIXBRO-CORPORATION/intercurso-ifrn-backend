from uuid import UUID

from business.match._correction_shared import (
    apply_event_correction,
    find_last_correctable_event,
    validate_match_correctable,
)
from business.match._shared import load_management_context
from core.business.audit.audit_logger import AuditLogger
from core.business.match.undo_last_event_port import UndoLastEventPort
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


class UndoLastEventAdapter(UndoLastEventPort):

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

        match = await validate_match_correctable(
            self.match_repository, match_id, monitor_id
        )

        target_event = await find_last_correctable_event(
            self.match_event_repository, match_id
        )

        result = await apply_event_correction(
            match,
            target_event,
            monitor_id,
            match_repository=self.match_repository,
            match_event_repository=self.match_event_repository,
            match_set_repository=self.match_set_repository,
            bracket_repository=self.bracket_repository,
            modality_repository=self.modality_repository,
            modality_configuration_repository=self.modality_configuration_repository,
            audit_logger=self.audit_logger,
            normal_audit_action=AuditAction.MATCH_EVENT_UNDONE,
        )

        context.put_property("corrected_event", result.corrected_event)
        if result.reactivated_player_id is not None:
            context.put_property("reactivated_player_id", result.reactivated_player_id)
        if result.correction_alert is not None:
            context.put_property("correction_alert", result.correction_alert)

        await load_management_context(
            context,
            result.match,
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

        return result.match
