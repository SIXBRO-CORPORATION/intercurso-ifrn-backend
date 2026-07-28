from pydantic import BaseModel, ConfigDict, Field


class SeasonFinishRequest(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    confirmation_name: str = Field(
        min_length=1,
        description="Deve corresponder exatamente ao nome da temporada",
    )
