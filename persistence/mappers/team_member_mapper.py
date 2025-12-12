from typing import Optional

from domain.team_member import TeamMember
from persistence.model.team_member_entity import TeamMemberEntity


class TeamMemberMapper:

    def to_domain(self, entity: Optional[TeamMemberEntity]) -> Optional[TeamMember]:
        if entity is None:
            return None

        return TeamMember(
            team_id=entity.team_id,
            user_id=entity.user_id,
            member_matricula=entity.member_matricula,
            member_name=entity.member_name,
            member_cpf=entity.member_cpf,
            active=entity.active
        )

    def to_entity(self, team_member: TeamMember) -> TeamMemberEntity:

        entity = TeamMemberEntity(
            team_id=team_member.team_id,
            user_id=team_member.user_id,
            member_matricula=team_member.member_matricula,
            member_name=team_member.member_name,
            member_cpf=team_member.member_cpf,
            active=team_member.active
        )

        return entity