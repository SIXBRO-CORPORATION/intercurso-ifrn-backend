from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, declared_attr
from datetime import datetime

class Base(DeclarativeBase):
    pass

class AbstractEntity(Base):

    __abstract__ = True

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now(),
    )

    modified_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now(),
        onupdate=datetime.now(),
    )

    active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    @declared_attr
    def __tablename__(cls) -> str:
        import re
        name = cls.__name__.replace('Entity', '')
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower() + 's'