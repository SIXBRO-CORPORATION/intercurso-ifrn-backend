from typing import Dict, List, Tuple
from uuid import UUID

from business.bracket._knockout_draw import (
    classified_teams_by_group,
    draw_knockout_pairs,
    find_first_round_knockout_slots,
    group_stage_pending_matches,
    knockout_stage_already_drawn,
)
from business.bracket._standings import order_group_standings
from core.business.audit.audit_logger import AuditLogger
from core.business.bracket.draw_knockout_stage_port import DrawKnockoutStagePort
from core.context import Context
from core.persistence.bracket.bracket_group_repository_port import (
    BracketGroupRepositoryPort,
)
from core.persistence.bracket.bracket_group_team_repository_port import (
    BracketGroupTeamRepositoryPort,
)
from core.persistence.bracket.bracket_repository_port import BracketRepositoryPort
from core.persistence.match.match_repository_port import MatchRepositoryPort
from domain.bracket.bracket import Bracket
from domain.bracket.bracket_group_team import BracketGroupTeam
from domain.enums.audit_action import AuditAction
from domain.enums.modality_format import ModalityFormat
from domain.exceptions.business_exception import BusinessException


class DrawKnockoutStageAdapter(DrawKnockoutStagePort):
    def __init__(
        self,
        bracket_repository: BracketRepositoryPort,
        bracket_group_repository: BracketGroupRepositoryPort,
        bracket_group_team_repository: BracketGroupTeamRepositoryPort,
        match_repository: MatchRepositoryPort,
        audit_logger: AuditLogger,
    ):
        self.bracket_repository = bracket_repository
        self.bracket_group_repository = bracket_group_repository
        self.bracket_group_team_repository = bracket_group_team_repository
        self.match_repository = match_repository
        self.audit_logger = audit_logger

    async def execute(self, context: Context) -> Bracket:
        bracket_id = context.get_property("bracket_id", UUID)
        requested_by = context.get_property("requested_by", UUID)
        if bracket_id is None:
            raise BusinessException("Identificador do chaveamento é obrigatório")

        bracket = await self.bracket_repository.get(bracket_id)
        if bracket is None:
            raise BusinessException("Chaveamento não encontrado")

        if bracket.format != ModalityFormat.GROUP_STAGE_KNOCKOUT:
            raise BusinessException(
                "Este chaveamento não possui fase de grupos para sortear o "
                "mata-mata"
            )

        matches = await self.match_repository.find_by_bracket(bracket_id)

        pending = group_stage_pending_matches(matches)
        if pending:
            raise BusinessException(
                "A fase de grupos ainda não foi concluída. Partida(s) de "
                f"grupo pendente(s): {len(pending)}"
            )

        first_round_slots = find_first_round_knockout_slots(matches)
        if not first_round_slots:
            raise BusinessException(
                "Não há partidas de mata-mata para receber os classificados "
                "neste chaveamento"
            )
        if knockout_stage_already_drawn(first_round_slots):
            raise BusinessException("O mata-mata deste chaveamento já foi sorteado")

        groups = await self.bracket_group_repository.find_by_bracket(bracket_id)
        if not groups:
            raise BusinessException("Chaveamento não possui grupos configurados")

        group_ids = [group.id for group in groups]
        all_group_teams = await self.bracket_group_team_repository.find_by_groups(
            group_ids
        )
        teams_by_group: Dict[UUID, List[BracketGroupTeam]] = {
            group_id: [] for group_id in group_ids
        }
        for group_team in all_group_teams:
            teams_by_group.setdefault(group_team.bracket_group_id, []).append(
                group_team
            )

        classified_per_group = (bracket.configuration or {}).get(
            "classified_per_group"
        )
        if not isinstance(classified_per_group, int) or classified_per_group < 1:
            raise BusinessException(
                "Configuração do chaveamento não define 'classified_per_group' "
                "corretamente"
            )

        groups_with_standings: List[Tuple[UUID, List[UUID]]] = []
        for group in groups:
            ordered = order_group_standings(teams_by_group[group.id], matches)
            if len(ordered) < classified_per_group:
                raise BusinessException(
                    f"Grupo '{group.name}' não tem times suficientes para "
                    f"classificar {classified_per_group}"
                )
            groups_with_standings.append(
                (group.id, [team.team_id for team in ordered])
            )

        classified_teams = classified_teams_by_group(
            groups_with_standings, classified_per_group
        )

        if len(classified_teams) != len(first_round_slots) * 2:
            raise BusinessException(
                "Número de classificados não corresponde ao número de vagas "
                "da 1ª rodada do mata-mata. Verifique a configuração do "
                "chaveamento."
            )

        pairs = draw_knockout_pairs(classified_teams)

        # N + 1?
        for slot, (team1_id, team2_id) in zip(first_round_slots, pairs):
            locked_slot = await self.match_repository.lock_for_update(slot.id)
            if locked_slot is None:
                continue
            locked_slot.team1_id = team1_id
            locked_slot.team2_id = team2_id
            await self.match_repository.save(locked_slot)

        await self.audit_logger.log(
            action=AuditAction.KNOCKOUT_STAGE_DRAWN,
            description=(
                f"Mata-mata sorteado para o chaveamento {bracket.id}: "
                f"{len(classified_teams)} time(s) classificado(s) em "
                f"{len(pairs)} confronto(s)"
            ),
            actor_id=requested_by,
        )

        context.put_property("classified_count", len(classified_teams))
        context.put_property("knockout_matches_filled", len(pairs))

        return bracket
