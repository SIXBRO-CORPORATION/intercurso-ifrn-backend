from pydantic import BaseModel, Field


class ModalityUpdateActiveRequest(BaseModel):
    active: bool = Field(
        description="Novo estado da modalidade: `true` para ativar, "
        "`false` para desativar."
    )
