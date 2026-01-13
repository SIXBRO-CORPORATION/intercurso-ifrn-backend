from typing import List

from core.business.team.create_team_members_port import CreateTeamMembersPort
from core.context import Context
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.donation_status import TeamMemberStatus
from domain.exceptions.business_exception import BusinessException
from domain.team import Team
from domain.team_member import TeamMember


class CreateTeamMembersAdapter(CreateTeamMembersPort):
    def __init__(
        self, repository: TeamMemberRepositoryPort, user_repository: UserRepositoryPort
    ):
        self.repository = repository
        self.user_repository = user_repository

    async def execute(self, context: Context) -> List[TeamMember]:
        members_data = context.get_property("members", list)
        saved_team = context.get_property("saved_team", Team)

        team_members = []
        for member_data in members_data:
            if not member_data.get("matricula"):
                raise BusinessException("Matrícula do membro é obrigatória")

            if not member_data.get("cpf") or member_data.get("cpf").strip() == "":
                raise BusinessException("CPF do membro é obrigatório")

            cpf = member_data.get("cpf").strip()
            if not cpf.isdigit() or len(cpf) != 11:
                raise BusinessException("CPF inválido. Deve conter 11 dígitos")

            existing_user = await self.user_repository.find_by_matricula(
                member_data.get("matricula")
            )
            user_id = existing_user.id if existing_user else None

            team_member = TeamMember(
                team_id=saved_team.id,
                user_id=user_id,
                member_matricula=member_data.get("matricula"),
                member_name=member_data.get("name").strip(),
                member_cpf=cpf,
                status=TeamMemberStatus.PENDING_DONATION,
            )

            saved_member = await self.repository.save(team_member)
            team_members.append(saved_member)

        context.put_property("members_count", len(team_members))
        context.put_property("team_members", team_members)

        return team_members
