from typing import Optional
from domain.abstract_domain import AbstractDomain
from domain.enums.user_role import UserRole
from dataclasses import dataclass, field


@dataclass
class User(AbstractDomain):
    name: str = None
    email: str = None
    cpf: str = None
    matricula: str = None
    atleta: bool = None
    role: UserRole = field(default=UserRole.USER)
    tipo_usuario: Optional[str] = None
    campus: Optional[str] = None
    curso: Optional[str] = None

    @classmethod
    def from_suap_dict(cls, data: dict) -> "User":
        vinculo = data.get("vinculo") or {}

        matricula = data.get("matricula")
        campus = vinculo.get("campus")
        curso = vinculo.get("curso")
        tipo_usuario = data.get("tipo_vinculo") or data.get("tipo_usuario")

        return cls(
            matricula=str(matricula),
            name=vinculo.get("nome"),
            email=data.get("email", ""),
            cpf=str(data.get("cpf", "")).replace(".", "").replace("-", ""),
            tipo_usuario=tipo_usuario,
            campus=campus,
            curso=curso,
        )
