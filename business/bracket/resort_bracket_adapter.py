from uuid import UUID

from business.bracket.engine.config_suggester import (
    resolve_configuration,
    validate_team_count_for_format,
)
from business.bracket.engine.draw_engine import build_draw
from core.business.bracket.resort_bracket_port import ResortBracketPort
from core.business.audit.audit_logger import AuditLogger
from core.context import Context
from core.persistence.bracket.bracket_group_repository_port import BracketGroupRepositoryPort
from core.persistence.bracket.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from core.persistence.team.team_repository_port import TeamRepositoryPort
from core.persistence.user.user_repository_port import UserRepositoryPort
from domain.bracket.bracket import Bracket
from domain.bracket.bracket_group import BracketGroup
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.enums.audit_action import AuditAction
from domain.enums.bracket_status import BracketStatus
from domain.enums.match_status import MatchStatus
from domain.enums.modality_format import ModalityFormat
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match


class ResortBracketAdapter(ResortBracketPort):
    def __init__(
        self,
        bracket_repository: BracketRepositoryPort,
        bracket_group_repository: BracketGroupRepositoryPort,
        bracket_group_team_repository: BracketGroupTeamRepositoryPort,
        match_repository: MatchRepositoryPort,
        team_repository: TeamRepositoryPort,
        user_repository: UserRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.bracket_repository = bracket_repository
        self.bracket_group_repository = bracket_group_repository
        self.bracket_group_team_repository = bracket_group_team_repository
        self.match_repository = match_repository
        self.team_repository = team_repository
        self.user_repository = user_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Bracket:
        bracket_id = context.get_property("bracket_id", UUID)
        requested_by = context.get_property("requested_by", UUID)
        if bracket_id is None:
            raise BusinessException("Chaveamento é obrigatório")

        bracket = await self.bracket_repository.get(bracket_id)
        if bracket is None:
            raise BusinessException("Chaveamento não encontrado")

        if bracket.status not in (BracketStatus.DRAFT, BracketStatus.ACTIVE):
            raise BusinessException(
                "Somente chaveamentos em rascunho ou ativos podem ser re-sorteados"
            )

        existing_matches = await self.match_repository.find_by_bracket(bracket.id)
        started_matches = [
            match for match in existing_matches if match.status != MatchStatus.SCHEDULED
        ]
        if started_matches:
            raise BusinessException(
                f"Não é possível re-sortear: {len(started_matches)} partida(s) já "
                "foram iniciadas ou finalizadas"
            )

        approved_teams = (
            await self.team_repository.find_approved_teams_by_season_and_modality(
                bracket.season_id, bracket.modality_id
            )
        )
        team_count = len(approved_teams)
        validate_team_count_for_format(bracket.format, team_count)

        configuration_override = dict(bracket.configuration or {})
        if bracket.format == ModalityFormat.GROUP_STAGE_KNOCKOUT:
            configuration_override.pop("group_sizes", None)

        resolved_config = resolve_configuration(
            bracket.format, team_count, configuration_override
        )

        team_ids = [team.id for team in approved_teams]
        draw_plan = build_draw(bracket.format, team_ids, resolved_config)

        await self.bracket_group_team_repository.delete_by_bracket(bracket.id)
        await self.bracket_group_repository.delete_by_bracket(bracket.id)
        await self.match_repository.delete_by_bracket(bracket.id)

        saved_group_ids: list = []
        for group_spec in draw_plan.groups:
            saved_group = await self.bracket_group_repository.save(
                BracketGroup(
                    bracket_id=bracket.id,
                    name=group_spec.name,
                    display_order=group_spec.display_order,
                )
            )
            saved_group_ids.append(saved_group.id)

            for team_id in group_spec.team_ids:
                await self.bracket_group_team_repository.save(
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
                )

        for match_spec in draw_plan.matches:
            bracket_group_id = (
                saved_group_ids[match_spec.group_index]
                if match_spec.group_index is not None
                else None
            )
            await self.match_repository.save(
                Match(
                    bracket_id=bracket.id,
                    bracket_group_id=bracket_group_id,
                    team1_id=match_spec.team1_id,
                    team2_id=match_spec.team2_id,
                    match_type=match_spec.match_type,
                    match_category=match_spec.match_category,
                    status=match_spec.status,
                    is_bye=match_spec.is_bye,
                    winner_id=match_spec.winner_id,
                    finished_at=match_spec.finished_at,
                    team1_score=0,
                    team2_score=0,
                    clock_seconds=0,
                    clock_running=False,
                    current_period=1,
                )
            )

        bracket.configuration = resolved_config
        saved_bracket = await self.bracket_repository.save(bracket)

        requesting_monitor = (
            await self.user_repository.get(requested_by) if requested_by else None
        )
        actor_role = (
            requesting_monitor.role.value
            if requesting_monitor is not None and requesting_monitor.role
            else None
        )
        await self.audit_logger.log(
            action=AuditAction.BRACKET_RESORTED,
            description=(
                f"Chaveamento re-sorteado para {team_count} time(s) aprovado(s)"
            ),
            actor_id=requested_by,
            actor_role=actor_role,
        )

        context.put_property("teams_count", team_count)
        context.put_property("groups_created", len(draw_plan.groups))
        context.put_property("matches_created", len(draw_plan.matches))
        context.put_property("byes_created", draw_plan.byes_created)

        return saved_bracket