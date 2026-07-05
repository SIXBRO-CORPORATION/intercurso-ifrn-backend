from typing import Optional
from domain.abstract_domain import AbstractDomain
from domain.enums.user_role import UserRole
from dataclasses import dataclass, field


@dataclass
class User(AbstractDomain):
    name: str = None
    email: str = None
    cpf: str = None
    matricula: int = None
    atleta: bool = None
    role: UserRole = field(default=UserRole.USER)
    tipo_usuario: Optional[str] = None
    campus: Optional[str] = None
    curso: Optional[str] = None

    @classmethod
    def from_suap_dict(cls, data: dict) -> "User":
        return cls(
            matricula=str(data.get("identificacao", "")),
            name=data.get("nome_usual", ""),
            email=data.get("email", ""),
            cpf=str(data.get("cpf", "")).replace(".", "").replace("-", ""),
            tipo_usuario=data.get("tipo_usuario"),
            campus=data.get("campus"),
            curso=data.get("curso"),
        )
