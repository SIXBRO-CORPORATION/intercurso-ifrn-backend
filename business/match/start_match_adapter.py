from datetime import datetime
from typing import List, Tuple
from uuid import UUID

from core.business.match.start_match_port import StartMatchPort
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
from domain.enums.event_type import EventType
from domain.enums.match_status import MatchStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.match import Match
from domain.match_event import MatchEvent
from domain.team_member import TeamMember
from domain.user import User


class StartMatchAdapter(StartMatchPort):
    def __init__(
        self,
        match_repository: MatchRepositoryPort,
        match_event_repository: MatchEventRepositoryPort,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
        bracket_repository: BracketRepositoryPort,
        modality_configuration_repository: ModalityConfigurationRepositoryPort,
        modality_repository: ModalityRepositoryPort,
    ):
        self.match_repository = match_repository
        self.match_event_repository = match_event_repository
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.bracket_repository = bracket_repository
        self.modality_configuration_repository = modality_configuration_repository
        self.modality_repository = modality_repository

    async def execute(self, context: Context) -> Match:
        match_id = context.get_property("match_id", UUID)
        monitor_id = context.get_property("monitor_id", UUID)

        if match_id is None:
            raise BusinessException("Partida é obrigatória")
        if monitor_id is None:
            raise BusinessException("Monitor responsável é obrigatório")

        match = await self.match_repository.get(match_id)
        if match is None:
            raise BusinessException("Partida não encontrada")

        # Regra de negócio 2: partida deve estar em SCHEDULED.
        if match.status != MatchStatus.SCHEDULED:
            status_atual = match.status.value if match.status else "desconhecido"
            raise BusinessException(
                "Somente partidas agendadas (SCHEDULED) podem ser iniciadas. "
                f"Status atual: {status_atual}"
            )

        if match.team1_id is None or match.team2_id is None:
            raise BusinessException(
                "A partida ainda não possui os dois times definidos"
            )

        team1 = await self.team_repository.get(match.team1_id)
        team2 = await self.team_repository.get(match.team2_id)

        if team1 is None or team2 is None:
            raise BusinessException("Um dos times da partida não foi encontrado")

        # Regra de negócio 3: ambos os times devem estar APPROVED.
        not_approved_teams = [
            team.name for team in (team1, team2) if team.status != TeamStatus.APPROVED
        ]
        if not_approved_teams:
            raise BusinessException(
                "Os seguintes times ainda não estão APPROVED: "
                + ", ".join(not_approved_teams)
            )

        # Regra de negócio 4: monitor só pode gerenciar uma partida IN_PROGRESS por vez.
        ongoing_match = await self.match_repository.find_in_progress_by_monitor(
            monitor_id
        )
        if ongoing_match is not None and ongoing_match.id != match.id:
            raise BusinessException(
                "Monitor já está gerenciando outra partida em andamento "
                f"(partida {ongoing_match.id})"
            )

        match.status = MatchStatus.IN_PROGRESS
        match.started_at = datetime.now()
        match.clock_seconds = 0
        match.clock_running = True
        match.current_period = 1
        match.team1_score = 0
        match.team2_score = 0
        match.monitor_id = monitor_id

        # TODO (débito técnico, mesmo padrão das fases anteriores): registro de
        # auditoria da operação (monitor, partida, data/hora) depende de
        # infraestrutura de auditoria ainda inexistente no projeto.
        saved_match = await self.match_repository.save(match)

        # Regra de negócio 8: cria evento MATCH_STARTED na timeline.
        match_start_event = MatchEvent(
            match_id=saved_match.id,
            event_type=EventType.MATCH_STARTED,
            clock_seconds=0,
            metadata={"monitor_id": str(monitor_id)},
        )
        saved_event = await self.match_event_repository.save(match_start_event)

        # TODO (débito técnico Fase 5/6): notificação via WebSocket para os canais
        # /matches/{match_id}/live e /seasons/{season_id}/live (regra de negócio 9)
        # e Push Notification para alunos (regra de negócio 10) dependem de
        # infraestrutura ainda inexistente no projeto (ver Fase 6 do planejamento).

        bracket = await self.bracket_repository.get(saved_match.bracket_id)

        modality = None
        modality_configuration = None
        if bracket is not None:
            modality = await self.modality_repository.get(bracket.modality_id)
            modality_configuration = (
                await self.modality_configuration_repository.find_by_modality(
                    bracket.modality_id
                )
            )

        team1_players = await self._load_players(team1.id)
        team2_players = await self._load_players(team2.id)

        context.put_property("team1", team1)
        context.put_property("team2", team2)
        context.put_property("team1_players", team1_players)
        context.put_property("team2_players", team2_players)
        if modality is not None:
            context.put_property("modality", modality)
        if modality_configuration is not None:
            context.put_property("modality_configuration", modality_configuration)
        context.put_property("match_start_event", saved_event)

        return saved_match

    async def _load_players(self, team_id: UUID) -> List[Tuple[TeamMember, User]]:
        members = await self.team_member_repository.find_members_by_team_id(team_id)
        players: List[Tuple[TeamMember, User]] = []
        for member in members:
            user = await self.user_repository.get(member.user_id)
            if user is not None:
                players.append((member, user))
        return players
