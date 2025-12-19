from sqlalchemy import Column, DateTime, Boolean, UUID
from sqlalchemy.orm import DeclarativeBase, declared_attr
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    pass


class AbstractEntity(Base):
    __abstract__ = True

    id = Column(UUID, primary_key=True, default=lambda: uuid.uuid4())

    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(),
    )

    modified_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
    )

    active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    @declared_attr
    def __tablename__(cls) -> str:
        import re

        name = cls.__name__.replace("Entity", "")
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower() + "s"
