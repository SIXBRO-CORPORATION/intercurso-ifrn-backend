from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SeasonReopenRequest(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    new_registration_end_date: datetime = Field()
