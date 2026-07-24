from datetime import datetime
from uuid import UUID

from business.match._shared import load_management_context, validate_match_in_progress
from core.business.match.end_period_port import EndPeriodPort
from core.context import Context
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.modality.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality.modality_repository_port import ModalityRepositoryPort
from core.persistence.team.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.enums.event_type import EventType
from domain.match.match import Match
from domain.match.match_event import MatchEvent


class EndPeriodAdapter(EndPeriodPort):
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
    ):
        self.match_repository = match_repository
        self.match_event_repository = match_event_repository
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.bracket_repository = bracket_repository
        self.modality_repository = modality_repository
        self.modality_configuration_repository = modality_configuration_repository

    async def execute(self, context: Context) -> Match:
        match_id = context.get_property("match_id", UUID)
        monitor_id = context.get_property("monitor_id", UUID)

        match = await validate_match_in_progress(
            self.match_repository, match_id, monitor_id
        )

        now = datetime.now()
        clock_seconds = match.current_clock_seconds(now)

        period_end_event = MatchEvent(
            match_id=match_id,
            event_type=EventType.PERIOD_END,
            clock_seconds=clock_seconds,
            metadata_json={"period": match.current_period},
        )
        await self.match_event_repository.save(period_end_event)

        match.clock_seconds = clock_seconds
        match.clock_running = False
        match.current_period = (match.current_period or 0) + 1
        saved_match = await self.match_repository.save(match)

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
        )

        return saved_match
