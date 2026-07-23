from datetime import datetime
from uuid import UUID

from core.business.team.confirm_donation_port import ConfirmDonationPort
from core.context import Context
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.donation_status import DonationStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team.team_member import TeamMember


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
        target_user_id = context.get_property("target_user_id", UUID)
        confirmed_by_user_id = context.get_property("confirmed_by_user_id", UUID)

        if team_id is None or target_user_id is None:
            raise BusinessException("Time e membro alvo são obrigatórios")

        team = await self.team_repository.get(team_id)
        if team is None:
            raise BusinessException("Time não encontrado")

        if team.status not in (TeamStatus.SUBMITTED, TeamStatus.APPROVED):
            raise BusinessException(
                "Doações só podem ser confirmadas para times submetidos ou aprovados"
            )

        member_user = await self.user_repository.get(target_user_id)
        if member_user is None:
            raise BusinessException("Usuário não encontrado")

        members = await self.team_member_repository.find_members_by_team_id(team_id)
        member = next(
            (m for m in members if m.user_id == member_user.id), None
        )
        if member is None:
            raise BusinessException("Esse usuário não é membro do time")

        if member.donation_status == DonationStatus.DONATION_CONFIRMED:
            raise BusinessException("Doação já confirmada para esse membro")

        member.donation_status = DonationStatus.DONATION_CONFIRMED
        member.donation_confirmed_at = datetime.now()
        member.donation_confirmed_by = confirmed_by_user_id

        updated_member = await self.team_member_repository.save(member)

        context.put_property("member_user", member_user)

        return updated_member
