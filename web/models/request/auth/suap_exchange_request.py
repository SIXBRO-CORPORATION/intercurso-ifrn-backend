from pydantic import BaseModel, Field


class SuapExchangeRequest(BaseModel):
    code: str = Field(..., description="Authorization code recebido do SUAP")
    state: str = Field(..., description="State retornado pelo SUAP")
