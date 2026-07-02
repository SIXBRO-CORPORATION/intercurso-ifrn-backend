from domain.team import Team
from domain.team_member import TeamMember
from domain.user import User
from web.models.response.team_member_response import TeamMemberResponse
from web.models.response.team_register_response import TeamRegisterResponse


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
