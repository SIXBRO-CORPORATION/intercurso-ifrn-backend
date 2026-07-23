from datetime import datetime
from uuid import UUID

from business.match._shared import (
    is_player_expelled,
    load_management_context,
    validate_match_in_progress,
    validate_player_in_team,
    validate_team_in_match,
)
from core.business.match.register_card_port import RegisterCardPort
from core.context import Context
from core.persistence.bracket_repository_port import BracketRepositoryPort
from core.persistence.match_event_repository_port import MatchEventRepositoryPort
from core.persistence.match_repository_port import MatchRepositoryPort
from core.persistence.modality_configuration_repository_port import (
    ModalityConfigurationRepositoryPort,
)
from core.persistence.modality_repository_port import ModalityRepositoryPort
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.card_type import CardType
from domain.enums.event_type import EventType
from domain.exceptions.business_exception import BusinessException
from domain.match import Match
from domain.match_event import MatchEvent


class RegisterCardAdapter(RegisterCardPort):
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
        team_id = context.get_property("team_id", UUID)
        player_id = context.get_property("player_id", UUID)
        card_type = context.get_property("card_type", CardType)

        if card_type is None:
            raise BusinessException("Tipo de cartão é obrigatório")

        match = await validate_match_in_progress(
            self.match_repository, match_id, monitor_id
        )
        await validate_team_in_match(match, team_id)
        await validate_player_in_team(self.team_member_repository, team_id, player_id)

        if await is_player_expelled(self.match_event_repository, match_id, player_id):
            raise BusinessException("Jogador já está expulso nesta partida")

        now = datetime.now()
        clock_seconds = match.current_clock_seconds(now)

        expulsion_reason = None
        previous_yellow_count = 0

        if card_type == CardType.YELLOW:

            previous_yellows = await self.match_event_repository.find_by_match_and_type(
                match_id, EventType.CARD_YELLOW
            )
            previous_yellow_count = sum(
                1 for event in previous_yellows if event.player_id == player_id
            )
            card_event_type = EventType.CARD_YELLOW
            if previous_yellow_count >= 1:
                expulsion_reason = "second_yellow"
        else:
            card_event_type = EventType.CARD_RED
            expulsion_reason = "direct_red"

        card_event = MatchEvent(
            match_id=match_id,
            team_id=team_id,
            player_id=player_id,
            event_type=card_event_type,
            clock_seconds=clock_seconds,
            metadata_json={"previous_cards": previous_yellow_count},
        )
        await self.match_event_repository.save(card_event)

        if expulsion_reason is not None:
            expulsion_event = MatchEvent(
                match_id=match_id,
                team_id=team_id,
                player_id=player_id,
                event_type=EventType.EXPULSION,
                clock_seconds=clock_seconds,
                metadata_json={
                    "triggered_by": expulsion_reason,
                    "auto_generated": expulsion_reason == "second_yellow",
                },
            )
            await self.match_event_repository.save(expulsion_event)

        await load_management_context(
            context,
            match,
            self.team_repository,
            self.team_member_repository,
            self.user_repository,
            self.bracket_repository,
            self.modality_repository,
            self.modality_configuration_repository,
            self.match_event_repository,
        )

        return match
