from typing import List

from domain.team import Team
from domain.team_member import TeamMember
from web.models.response.team_member_response import TeamMemberResponse
from web.models.response.team_register_response import TeamRegisterResponse


class TeamModelMapper:
    def to_register_response(
            self,
            team: Team,
            members: List[TeamMember]
    ) -> TeamRegisterResponse:
        member_responses = [
            TeamMemberResponse(
                matricula=member.member_matricula,
                name=member.member_name,
                cpf=member.member_cpf,
                status=member.status.value,
                user_id=member.user_id,
                is_registered=member.user_id is not None
            )
            for member in members
        ]

        return TeamRegisterResponse(
            team_id=team.id,
            name=team.name,
            modality=team.modality.value,
            status=team.status.value,
            photo=team.photo,
            members_count=len(members),
            members=member_responses,
            message="Time cadastrado com sucesso! Aguardando aprovação do monitor."
        )