from datetime import datetime
from typing import List

from core.business.team.create_team_members_port import CreateTeamMembersPort
from core.business.team.create_team_port import CreateTeamPort
from core.context import Context
from core.persistence.team_member_repository_port import TeamMemberRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from core.persistence.user_repository_port import UserRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.team import Team


class CreateTeamAdapter(CreateTeamPort):
    def __init__(
            self,
            team_repository: TeamRepositoryPort,
            team_member_repository: TeamMemberRepositoryPort,
            user_repository: UserRepositoryPort,
            create_team_members_port: CreateTeamMembersPort
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_repository = user_repository
        self.create_team_members_port = create_team_members_port

    async def execute(self, context: Context) -> Team:
        team_data = context.get_data(Team)
        members_data = context.get_property("members", list)

        if team_data is None:
            raise BusinessException("Dados do time são obrigatórios")

        if not members_data or len(members_data) == 0:
            raise BusinessException("O time deve ter pelo menos um membro")

        if not team_data.name or team_data.name.strip() == "":
            raise BusinessException("Nome do time é obrigatório")

        if team_data.modality is None:
            raise BusinessException("Modalidade é obrigatória")

        await self._validate_members_not_in_same_modality(members_data, team_data.modality)

        new_team = Team(
            name=team_data.name.strip(),
            photo=team_data.photo,
            modality=team_data.modality,
            status=TeamStatus.PENDING,
            created_at=datetime.now(),
            modified_at=None,
            active=True
        )

        saved_team = await self.team_repository.save(new_team)

        context.put_property("saved_team", saved_team)

        await self.create_team_members_port.execute(context)

        context.put_property("team_id", saved_team.id)
        context.put_property("team_created", True)

        return saved_team

    async def _validate_members_not_in_same_modality(
            self,
            members_data: List[dict],
            modality
    ) -> None:
        for member_data in members_data:
            matricula = member_data.get("matricula")
            if not matricula:
                continue

            existing_teams = await self.team_repository.find_teams_by_matricula(matricula)

            for team in existing_teams:
                if team.modality == modality:
                    raise BusinessException(
                        f"O membro com matrícula {matricula} já está cadastrado"
                        f"em outro time de {modality.value}"
                    )