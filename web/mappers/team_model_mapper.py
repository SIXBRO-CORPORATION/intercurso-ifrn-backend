from typing import Optional

from domain.modality import Modality
from domain.team import Team
from domain.team.team_member import TeamMember
from domain.user import User
from web.models.response.team.team_invite_preview_response import (
    TeamInvitePreviewResponse,
)
from web.models.response.team.team_join_response import TeamJoinResponse
from web.models.response.team.team_member_response import TeamMemberResponse
from web.models.response.team.team_register_response import TeamRegisterResponse


class TeamModelMapper:
    def to_register_response(
        self, team: Team, owner_member: TeamMember, owner_user: User
    ) -> TeamRegisterResponse:
        return TeamRegisterResponse(
            team_id=team.id,
            name=team.name,
            modality_id=team.modality_id,
            status=team.status.value,
            photo=team.photo,
            invite_token=team.invite_token,
            owner_id=team.owner_id,
            message="Time cadastrado com sucesso! Compartilhe o link de convite com os demais membros.",
        )

    def to_member_response(
        self, member: TeamMember, user: User
    ) -> TeamMemberResponse:
        return TeamMemberResponse(
            user_id=member.user_id,
            name=user.name,
            matricula=user.matricula,
            role=member.role.value,
            donation_status=member.donation_status.value,
        )

    def to_invite_preview_response(
        self,
        team: Team,
        modality: Optional[Modality],
        members_count: int,
        owner_user: Optional[User],
        captain_user: Optional[User],
    ) -> TeamInvitePreviewResponse:
        return TeamInvitePreviewResponse(
            team_id=team.id,
            name=team.name,
            modality_id=team.modality_id,
            modality_name=modality.name if modality else None,
            photo=team.photo,
            members_count=members_count,
            max_members=modality.max_members if modality else None,
            captain_name=captain_user.name if captain_user else None,
            owner_name=owner_user.name if owner_user else None,
        )

    def to_join_response(self, team: Team, member: TeamMember) -> TeamJoinResponse:
        return TeamJoinResponse(
            team_id=team.id,
            team_name=team.name,
            role=member.role.value,
            donation_status=member.donation_status.value,
            joined_at=member.joined_at,
            message="Você entrou no time com sucesso!",
        )
