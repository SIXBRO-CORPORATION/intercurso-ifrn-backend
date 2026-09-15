from pydantic import BaseModel, ConfigDict, Field


class LiveTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket: str = Field(description="Ticket de uso único e curta duração para abrir o SSE")
    expires_in_seconds: int = Field(
        description="Validade do ticket em segundos a partir da emissão"
    )
