from typing import Optional
from domain.abstract_domain import AbstractDomain
from dataclasses import dataclass

@dataclass
class User(AbstractDomain):

    name: str = None
    email: str = None
    cpf: str = None
    matricula: int = None
    atleta: bool = None
    tipo_usuario: Optional[str] = None
    campus: Optional[str] = None
    curso: Optional[str] = None

    @staticmethod
    def from_suap_dict(cls, data: dict) -> "User":
        return cls(
            matricula=str(data.get("identificacao", "")),
            nome_usual=data.get("nome_usual", ""),
            email=data.get("email", ""),
            cpf=str(data.get("cpf", "")).replace(".", "").replace("-", ""),
            tipo_usuario=data.get("tipo_usuario"),
            campus=data.get("campus"),
        )