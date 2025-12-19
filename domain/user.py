from typing import Optional
from domain.abstract_domain import AbstractDomain
from dataclasses import dataclass


@dataclass
class User(AbstractDomain):
    name: str = None
    email: str = None
    cpf: str = None
    matricula: str = None
    atleta: bool = None
    tipo_usuario: Optional[str] = None
    campus: Optional[str] = None
    curso: Optional[str] = None
