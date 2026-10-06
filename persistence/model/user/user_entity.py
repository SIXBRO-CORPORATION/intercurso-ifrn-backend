from sqlalchemy import Column, String, Boolean, Date, Integer
from persistence.model.abstract_entity import AbstractEntity


class UserEntity(AbstractEntity):
    __tablename__ = "users"

    name = Column(String(255), nullable=False)

    email = Column(String(255), index=True)

    cpf = Column(String(11), nullable=False, unique=True, index=True)

    matricula = Column(String(14), nullable=False, unique=True, index=True)

    atleta = Column(Boolean, nullable=False, default=False)

    role = Column(String(20), nullable=False, default="USER", index=True)

    gender = Column(String(1), nullable=True)

    tipo_usuario = Column(String(50), nullable=True)

    campus = Column(String(50), nullable=True)

    curso = Column(String(255), nullable=True)

    turno = Column(String(50), nullable=True)

    email_classroom = Column(String(255), nullable=True)

    photo = Column(String, nullable=True)

    birth_date = Column(Date, nullable=True)

    frequencia_percentual = Column(Integer, nullable=True)
