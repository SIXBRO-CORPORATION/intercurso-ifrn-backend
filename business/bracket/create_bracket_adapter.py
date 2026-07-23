from datetime import datetime
from uuid import UUID

from business.bracket.engine.config_suggester import (
    resolve_configuration,
    validate_team_count_for_format,
)
from business.bracket.engine.draw_engine import build_draw
from core.business.bracket.create_bracket_port import CreateBracketPort
from core.context import Context
from core.persistence.bracket_group_repository_port import BracketGroupRepositoryPort
from core.persistence.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from core.persistence.bracket_repository_port import BracketRepositoryPort
from core.persistence.match_repository_port import MatchRepositoryPort
from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season_repository_port import SeasonRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from domain.bracket.bracket import Bracket
from domain.bracket.bracket_group import BracketGroup
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.enums.bracket_status import BracketStatus
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException
from domain.match.match import Match


class CreateBracketAdapter(CreateBracketPort):
    def __init__(
        self,
        bracket_repository: BracketRepositoryPort,
        bracket_group_repository: BracketGroupRepositoryPort,
        bracket_group_team_repository: BracketGroupTeamRepositoryPort,
        match_repository: MatchRepositoryPort,
        team_repository: TeamRepositoryPort,
        season_repository: SeasonRepositoryPort,
        season_modality_repository: SeasonModalityRepositoryPort,
    ):
        self.bracket_repository = bracket_repository
        self.bracket_group_repository = bracket_group_repository
        self.bracket_group_team_repository = bracket_group_team_repository
        self.match_repository = match_repository
        self.team_repository = team_repository
        self.season_repository = season_repository
        self.season_modality_repository = season_modality_repository

    async def execute(self, context: Context) -> Bracket:
        bracket_shell = context.get_data(Bracket)
        created_by = context.get_property("created_by", UUID)
        configuration_override = context.get_property("configuration", dict)

        if bracket_shell is None:
            raise BusinessException("Dados do chaveamento são obrigatórios")
        if bracket_shell.modality_id is None:
            raise BusinessException("Modalidade é obrigatória")
        if bracket_shell.format is None:
            raise BusinessException("Formato do chaveamento é obrigatório")
        if created_by is None:
            raise BusinessException("Monitor responsável é obrigatório")

        active_season = await self.season_repository.find_active_season()
        if active_season is None:
            raise BusinessException("Não há uma temporada ativa no momento")

        if active_season.status == SeasonStatus.REGISTRATION_OPEN:
            raise BusinessException(
                "Período de inscrições ainda está aberto. Aguarde o encerramento."
            )
        if active_season.status not in (
            SeasonStatus.REGISTRATION_CLOSED,
            SeasonStatus.IN_PROGRESS,
        ):
            raise BusinessException(
                "Temporada precisa estar com inscrições encerradas ou em "
                "andamento para criar um chaveamento"
            )

        modality_in_season = (
            await self.season_modality_repository.exists_by_season_and_modality(
                active_season.id, bracket_shell.modality_id
            )
        )
        if not modality_in_season:
            raise BusinessException(
                "Modalidade informada não faz parte da temporada ativa"
            )

        if await self.bracket_repository.exists_active_bracket_for_modality(
            active_season.id, bracket_shell.modality_id
        ):
            raise BusinessException(
                "Já existe um chaveamento ativo criado para essa modalidade"
            )

        approved_teams = (
            await self.team_repository.find_approved_teams_by_season_and_modality(
                active_season.id, bracket_shell.modality_id
            )
        )
        team_count = len(approved_teams)

        validate_team_count_for_format(bracket_shell.format, team_count)

        resolved_config = resolve_configuration(
            bracket_shell.format, team_count, configuration_override
        )

        team_ids = [team.id for team in approved_teams]
        draw_plan = build_draw(bracket_shell.format, team_ids, resolved_config)

        existing_brackets_in_season = await self.bracket_repository.find_by_season(
            active_season.id
        )
        is_first_bracket_of_season = len(existing_brackets_in_season) == 0

        new_bracket = Bracket(
            season_id=active_season.id,
            modality_id=bracket_shell.modality_id,
            format=bracket_shell.format,
            configuration=resolved_config,
            status=BracketStatus.ACTIVE,
            created_by=created_by,
        )
        saved_bracket = await self.bracket_repository.save(new_bracket)

        saved_group_ids: list = []
        for group_spec in draw_plan.groups:
            saved_group = await self.bracket_group_repository.save(
                BracketGroup(
                    bracket_id=saved_bracket.id,
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
                    bracket_id=saved_bracket.id,
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

        season_transitioned = False
        if (
            is_first_bracket_of_season
            and active_season.status == SeasonStatus.REGISTRATION_CLOSED
        ):
            active_season.status = SeasonStatus.IN_PROGRESS
            active_season.started_at = datetime.now()
            await self.season_repository.save(active_season)
            season_transitioned = True

        # TODO (débito técnico, mesmo padrão das fases anteriores): notificação
        # "🏆 Chaveamento publicado!" / "🏆 Fase de jogos iniciada!" aos alunos e
        # registro de auditoria (monitor, data/hora, configuração) dependem de
        # infraestrutura ainda inexistente no projeto (mesma dívida já assumida
        # nas Fases 1 e 3).

        context.put_property("teams_count", team_count)
        context.put_property("groups_created", len(draw_plan.groups))
        context.put_property("matches_created", len(draw_plan.matches))
        context.put_property("byes_created", draw_plan.byes_created)
        context.put_property("season_transitioned_to_in_progress", season_transitioned)

        return saved_bracket
