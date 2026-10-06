from typing import List, Optional
from uuid import UUID, uuid4

from business.bracket.engine.draw_engine import GroupSpec, MatchSpec
from core.persistence.bracket.bracket_group_repository_port import BracketGroupRepositoryPort
from core.persistence.bracket.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from core.persistence.match.match_repository_port import MatchRepositoryPort
from domain.bracket.bracket_group import BracketGroup
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.match.match import Match


async def persist_draw_groups(
    group_repository: BracketGroupRepositoryPort,
    group_team_repository: BracketGroupTeamRepositoryPort,
    bracket_id: UUID,
    group_specs: List[GroupSpec],
) -> List[UUID]:
    saved_groups = await group_repository.insert_all(
        [
            BracketGroup(
                bracket_id=bracket_id,
                name=spec.name,
                display_order=spec.display_order,
            )
            for spec in group_specs
        ]
    )
    await group_team_repository.insert_all(
        [
            BracketGroupTeam(
                bracket_group_id=saved_group.id,
                team_id=team_id,
                points=0,
                wins=0,
                draws=0,
                losses=0,
                goals_for=0,
                goals_against=0,
                goals_difference=0,
            )
            for spec, saved_group in zip(group_specs, saved_groups)
            for team_id in spec.team_ids
        ]
    )
    return [saved_group.id for saved_group in saved_groups]


async def persist_draw_matches(
    match_repository: MatchRepositoryPort,
    bracket_id: UUID,
    saved_group_ids: List[UUID],
    match_specs: List[MatchSpec],
) -> List[Match]:

    match_ids = [uuid4() for _ in match_specs]

    matches: List[Match] = []
    for match_spec, match_id in zip(match_specs, match_ids):
        bracket_group_id = (
            saved_group_ids[match_spec.group_index]
            if match_spec.group_index is not None
            else None
        )
        next_match_id: Optional[UUID] = (
            match_ids[match_spec.next_match_index]
            if match_spec.next_match_index is not None
            else None
        )

        matches.append(
            Match(
                id=match_id,
                bracket_id=bracket_id,
                bracket_group_id=bracket_group_id,
                team1_id=match_spec.team1_id,
                team2_id=match_spec.team2_id,
                match_type=match_spec.match_type,
                match_category=match_spec.match_category,
                status=match_spec.status,
                is_bye=match_spec.is_bye,
                winner_id=match_spec.winner_id,
                finished_at=match_spec.finished_at,
                next_match_id=next_match_id,
                team1_score=0,
                team2_score=0,
                clock_seconds=0,
                clock_running=False,
                current_period=1,
            )
        )

    return await match_repository.insert_all(matches)
