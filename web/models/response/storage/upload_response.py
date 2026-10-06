from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    object_key: str = Field(
        description=(
            "Chave do objeto no storage. É este valor (não uma URL) que deve "
            "ser enviado no campo `photo` de POST /api/team/."
        )
    )
    preview_url: str = Field(
        description=(
            "URL assinada e temporária, só para pré-visualizar a imagem "
            "logo após o upload. Expira e não deve ser persistida."
        )
    )
