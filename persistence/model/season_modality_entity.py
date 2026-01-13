from sqlalchemy import Column, DateTime, ForeignKey, func
import uuid
from uuid import UUID

class SeasonModalityEntity:
    __tablename__ = "season_modalities"

    id = Column(UUID, primary_key=True, default=lambda: uuid.uuid4())

    season_id = Column(ForeignKey("seasons.id"), nullable=False)
    
    modality_id = Column(ForeignKey("modalities.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)