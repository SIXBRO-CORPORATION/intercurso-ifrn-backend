from typing import Optional
from domain.team_member import TeamMember
from domain.enums.team_member_role import TeamMemberRole
from domain.enums.donation_status import DonationStatus
from persistence.model.team_member_entity import TeamMemberEntity

class TeamMemberMapper:
    def to_domain(self, entity: Optional[TeamMemberEntity]) -> Optional[TeamMember]:
        if entity is None:
            return None

        return TeamMember(
            id=entity.id,
            team_id=entity.team_id,
            user_id=entity.user_id,
            role=TeamMemberRole(entity.role) if entity.role else None,
            donation_status=DonationStatus(entity.donation_status) if entity.donation_status else None,
            donation_confirmed_at=entity.donation_confirmed_at,
            donation_confirmed_by=entity.donation_confirmed_by,
            joined_at=entity.joined_at,
            created_at=entity.created_at,
            modified_at=entity.modified_at,
            active=entity.active
        )

    def to_entity(self, domain: TeamMember) -> TeamMemberEntity:
        if domain is None:
            return None

        return TeamMemberEntity(
            id=domain.id,
            team_id=domain.team_id,
            user_id=domain.user_id,
            role=domain.role.value if domain.role else None,
            donation_status=domain.donation_status.value if domain.donation_status else None,
            donation_confirmed_at=domain.donation_confirmed_at,
            donation_confirmed_by=domain.donation_confirmed_by,
            joined_at=domain.joined_at,
            created_at=domain.created_at,
            modified_at=domain.modified_at,
            active=domain.active
        )