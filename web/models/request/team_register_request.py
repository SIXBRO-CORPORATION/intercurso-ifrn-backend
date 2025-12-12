from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from domain.enums.modality import ModalityType
from domain.team_member import TeamMember


class TeamRegisterRequest(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    name: str = Field()
    photo: Optional[str] = Field()
    modality: ModalityType = Field()
    members: List[TeamMember] = Field()