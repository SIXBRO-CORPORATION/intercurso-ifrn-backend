from sqlalchemy import Column, String, Integer, UUID
import uuid
from persistence.model.abstract_entity import AbstractEntity


class UserEntity(AbstractEntity):

    __tablename__ = "users"

    id = Column(
        UUID,
        primary_key=True,
        default=uuid.uuid4()
    )

    name = Column(
        String(255),
        nullable=False
    )

    email = Column(
        String(255),
        index=True
    )

    cpf = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True
    )

    matricula = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True
    )



