from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class AuthToken:
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None
    user_id: Optional[UUID] = None


@dataclass
class SUAPUserData:
    # Campos principais
    matricula: str
    nome_usual: str
    email: str
    cpf: str

    # Campos adicionais (podem variar)
    tipo_usuario: Optional[str] = None  # "Aluno", "Servidor", etc.
    campus: Optional[str] = None
    curso: Optional[str] = None

    # Vinculo original do SUAP
    vinculo: Optional[dict] = None