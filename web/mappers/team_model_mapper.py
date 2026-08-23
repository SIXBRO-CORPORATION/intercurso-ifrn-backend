from typing import Dict, List, Optional
from uuid import UUID

from domain.enums.donation_status import DonationStatus
from domain.modality.modality import Modality
from domain.team.team import Team
from domain.team.team_member import TeamMember
from domain.user.user import User
from web.models.response.team.team_details_response import TeamDetailsResponse
from web.models.response.team.team_invite_preview_response import (
    TeamInvitePreviewResponse,
)
from web.models.response.team.team_join_response import TeamJoinResponse
from web.models.response.team.team_member_response import TeamMemberResponse
from web.models.response.team.team_register_response import TeamRegisterResponse
from web.models.response.team.team_summary_response import TeamSummaryResponse


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

    def to_summary_response(self, team: Team, extra_info: dict) -> TeamSummaryResponse:
        return TeamSummaryResponse(
            team_id=team.id,
            name=team.name,
            season_id=team.season_id,
            modality_id=team.modality_id,
            modality_name=extra_info.get("modality_name"),
            status=team.status.value,
            owner_id=team.owner_id,
            owner_name=extra_info.get("owner_name"),
            members_count=extra_info.get("members_count", 0),
            donations_confirmed=extra_info.get("donations_confirmed", 0),
            donations_total=extra_info.get("donations_total", 0),
            submmited_at=team.submmited_at,
        )

    def to_details_response(
        self,
        team: Team,
        modality: Optional[Modality],
        members: List[TeamMember],
        member_users_by_id: Dict[UUID, User],
        owner_user: Optional[User],
        captain_user: Optional[User],
    ) -> TeamDetailsResponse:
        member_responses = [
            self.to_member_response(member, member_users_by_id[member.user_id])
            for member in members
            if member.user_id in member_users_by_id
        ]
        donations_total = len(member_responses)
        donations_confirmed = sum(
            1
            for member in members
            if member.donation_status == DonationStatus.DONATION_CONFIRMED
        )

        return TeamDetailsResponse(
            team_id=team.id,
            name=team.name,
            season_id=team.season_id,
            modality_id=team.modality_id,
            modality_name=modality.name if modality else None,
            photo=team.photo,
            status=team.status.value,
            owner_id=team.owner_id,
            owner_name=owner_user.name if owner_user else None,
            captain_id=team.captain_id,
            captain_name=captain_user.name if captain_user else None,
            token_active=team.token_active,
            submmited_at=team.submmited_at,
            approved_at=team.approved_at,
            rejected_at=team.rejected_at,
            members=member_responses,
            donations_confirmed=donations_confirmed,
            donations_total=donations_total,
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
