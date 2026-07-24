from datetime import datetime
from uuid import UUID

from business.match._shared import (
    load_management_context,
    load_modality_configuration,
    load_volleyball_configuration,
    validate_match_in_progress,
)
from core.business.match.end_set_port import EndSetPort
from core.context import Context
from core.persistence.bracket_repository_port import BracketRepositoryPort
from core.persistence.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match_repository_port import MatchRepositoryPort
from core.persistence.match_set_repository_port import MatchSetRepositoryPort
from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from core.persistence.volleyball_modality_configuration_repository_port import (
    VolleyballModalityConfigurationRepositoryPort,
)
from domain.enums.event_type import EventType
from domain.enums.score_type import ScoreType
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match
from domain.match.match_event import MatchEvent
from domain.match.match_set import MatchSet


class EndSetAdapter(EndSetPort):
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

        match = await validate_match_in_progress(
            self.match_repository, match_id, monitor_id
        )

        _, modality_configuration = await load_modality_configuration(
            self.bracket_repository,
            self.modality_repository,
            self.modality_configuration_repository,
            match.bracket_id,
        )
        if (
            modality_configuration is None
            or modality_configuration.score_type != ScoreType.SETS
        ):
            raise BusinessException(
                "Esta modalidade não usa sistema de sets (vôlei)"
            )

        volleyball_configuration = await load_volleyball_configuration(
            self.volleyball_modality_configuration_repository,
            modality_configuration,
        )
        points_per_set = volleyball_configuration.points_per_set
        final_set_points = volleyball_configuration.final_set_points
        sets_to_win = volleyball_configuration.sets_to_win

        team1_points = match.team1_score or 0
        team2_points = match.team2_score or 0

        existing_sets = await self.match_set_repository.find_by_match(match_id)
        current_set_number = len(existing_sets) + 1

        is_final_set = current_set_number == (2 * sets_to_win - 1)
        points_required = final_set_points if is_final_set else points_per_set

        winner_team_id = None
        if team1_points >= points_required and team1_points - team2_points >= 2:
            winner_team_id = match.team1_id
        elif team2_points >= points_required and team2_points - team1_points >= 2:
            winner_team_id = match.team2_id

        if winner_team_id is None:
            raise BusinessException(
                "Pontuação do set ainda não atinge os critérios de fim de set "
                f"({points_required} pontos com diferença mínima de 2). "
                f"Placar atual: {team1_points}x{team2_points}"
            )

        now = datetime.now()
        clock_seconds = match.current_clock_seconds(now)

        new_match_set = MatchSet(
            match_id=match_id,
            set_number=current_set_number,
            team1_points=team1_points,
            team2_points=team2_points,
            winner_team_id=winner_team_id,
        )
        saved_match_set = await self.match_set_repository.save(new_match_set)

        team1_sets_won = match.team1_sets_won or 0
        team2_sets_won = match.team2_sets_won or 0
        if winner_team_id == match.team1_id:
            team1_sets_won += 1
        else:
            team2_sets_won += 1
        match.team1_sets_won = team1_sets_won
        match.team2_sets_won = team2_sets_won

        match.team1_score = 0
        match.team2_score = 0

        match.sync_clock(now)
        saved_match = await self.match_repository.save(match)

        winner_sets_won = (
            team1_sets_won if winner_team_id == match.team1_id else team2_sets_won
        )

        set_end_event = MatchEvent(
            match_id=match_id,
            team_id=winner_team_id,
            event_type=EventType.SET_END,
            clock_seconds=clock_seconds,
            metadata_json={
                "set_number": current_set_number,
                "score": f"{team1_points}x{team2_points}",
                "winner_team_id": str(winner_team_id),
                "team1_sets_won": team1_sets_won,
                "team2_sets_won": team2_sets_won,
            },
        )
        await self.match_event_repository.save(set_end_event)

        context.put_property(
            "match_point_reached", winner_sets_won >= sets_to_win
        )
        context.put_property("last_finished_set", saved_match_set)

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
