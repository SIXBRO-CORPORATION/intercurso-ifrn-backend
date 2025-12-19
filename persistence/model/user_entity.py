from sqlalchemy import Column, String, Integer, Boolean
import uuid
from persistence.model.abstract_entity import AbstractEntity


class UserEntity(AbstractEntity):

    __tablename__ = "users"

    name = Column(
        String(255),
        nullable=False
    )

    email = Column(
        String(255),
        index=True
    )

    cpf = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    matricula = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    atleta = Column(
        Boolean,
        nullable=False,
        default=False
    )



