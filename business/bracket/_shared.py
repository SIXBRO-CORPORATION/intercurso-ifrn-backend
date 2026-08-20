from typing import List, Optional
from uuid import UUID, uuid4

from business.bracket.engine.draw_engine import MatchSpec
from core.persistence.match.match_repository_port import MatchRepositoryPort
from domain.match.match import Match


async def persist_draw_matches(
    match_repository: MatchRepositoryPort,
    bracket_id: UUID,
    saved_group_ids: List[UUID],
    match_specs: List[MatchSpec],
) -> List[Match]:

    match_ids = [uuid4() for _ in match_specs]

    saved_matches: List[Match] = []
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

        saved_match = await match_repository.save(
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
        saved_matches.append(saved_match)

    return saved_matches
