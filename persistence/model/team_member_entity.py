from sqlalchemy import Column, ForeignKey, String, Boolean

from persistence.model.abstract_entity import Base


class TeamMemberEntity(Base):

    __tablename__ = "team_members"

    team_id = Column(
        ForeignKey('teams.id'),
        primary_key=True
    )

    user_id = Column(
        ForeignKey('users.id')
    )

    member_matricula = Column(
        ForeignKey('users.matricula'),
        String(255),
        primary_key=True
    )

    member_name = Column(
        String(255),
        nullable=False
    )

    member_cpf = Column(
        String(14),
        nullable=False
    )

    active = Column(
        Boolean,
        nullable=False,
        default=False
    )