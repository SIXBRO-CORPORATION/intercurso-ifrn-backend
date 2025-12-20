from sqlalchemy import Column, ForeignKey, String, Enum, Integer

from domain.enums.team_member_status import TeamMemberStatus
from persistence.model.abstract_entity import Base


class TeamMemberEntity(Base):
    __tablename__ = "team_members"

    team_id = Column(ForeignKey("teams.id"), primary_key=True)

    user_id = Column(ForeignKey("users.id"))

    member_matricula = Column(Integer, ForeignKey("users.matricula"), primary_key=True)

    member_name = Column(String(255), nullable=False)

    member_cpf = Column(String(14), nullable=False)

    status = Column(Enum(TeamMemberStatus), nullable=False)
