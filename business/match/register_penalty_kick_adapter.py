from datetime import datetime
from uuid import UUID

from business.match._finish_shared import ensure_penalty_shootout_active
from business.match._shared import (
    load_management_context,
    validate_match_in_progress,
    validate_player_in_team,
    validate_team_in_match,
)
from core.business.match.register_penalty_kick_port import RegisterPenaltyKickPort
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
from domain.enums.event_type import EventType
from domain.enums.penalty_kick_result import PenaltyKickResult
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.match.match_event import MatchEvent


class RegisterPenaltyKickAdapter(RegisterPenaltyKickPort):

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

    async def execute(self, context: Context) -> Match:
        match_id = context.get_property("match_id", UUID)
        monitor_id = context.get_property("monitor_id", UUID)
        team_id = context.get_property("team_id", UUID)
        player_id = context.get_property("player_id", UUID)
        result = context.get_property("result", PenaltyKickResult)

        if result is None:
            raise BusinessException("Resultado da cobrança (GOAL ou MISS) é obrigatório")

        match = await validate_match_in_progress(
            self.match_repository, match_id, monitor_id
        )
        ensure_penalty_shootout_active(match)
        await validate_team_in_match(match, team_id)

        if player_id is not None:
            await validate_player_in_team(
                self.team_member_repository, team_id, player_id
            )

        scored = result == PenaltyKickResult.GOAL
        if team_id == match.team1_id:
            if scored:
                match.team1_penalty_score = (match.team1_penalty_score or 0) + 1
        else:
            if scored:
                match.team2_penalty_score = (match.team2_penalty_score or 0) + 1

        now = datetime.now()
        clock_seconds = match.current_clock_seconds(now)

        saved_match = await self.match_repository.save(match)

        kick_event = MatchEvent(
            match_id=match_id,
            team_id=team_id,
            player_id=player_id,
            event_type=EventType.PENALTY_GOAL if scored else EventType.PENALTY_MISS,
            clock_seconds=clock_seconds,
            metadata_json={
                "team1_penalty_score": saved_match.team1_penalty_score,
                "team2_penalty_score": saved_match.team2_penalty_score,
            },
        )
        await self.match_event_repository.save(kick_event)

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
