from uuid import UUID

from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.context import Context
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.team_member_status import TeamMemberStatus
from domain.exceptions.business_exception import BusinessException
from domain.team_member import TeamMember


class ConfirmDonationAdapter(ConfirmDonationPort):
    def __init__(
        self,
        team_repository: TeamRepositoryPort,
        team_member_repository: TeamMemberRepositoryPort,
        user_repository: UserRepositoryPort,
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository

    async def execute(self, context: Context) -> TeamMember:
        team_id = context.get_property("team_id", UUID)
        matricula = context.get_property("matricula", int)

        if team_id is None:
            raise Exception("ID do time é obrigatório")

        if matricula is None:
            raise BusinessException("Matrícula do membro é obrigatória")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        member = await self.team_member_repository.find_member_by_matricula_and_team_id(
            matricula, team_id
        )

        if member is None:
            raise BusinessException(
                f"Membro com matrícula {matricula} não encontrado neste time"
            )

        if member.status == TeamMemberStatus.DONATION_CONFIRMED:
            raise BusinessException("Doação já foi confirmada para este membro")

        updated_member = TeamMember(
            team_id=member.team_id,
            user_id=member.user_id,
            member_matricula=member.member_matricula,
            member_name=member.member_name,
            member_cpf=member.member_cpf,
            status=TeamMemberStatus.DONATION_CONFIRMED,
        )

        saved_member = await self.team_member_repository.save(updated_member)

        if saved_member.user_id:
            user = await self.user_repository.get(saved_member.user_id)
            if user:
                user.atleta = True
                await self.user_repository.save(user)

        context.put_property("donation_confirmed", True)
        context.put_property("user_updated", saved_member.user_id is not None)

        return saved_member
