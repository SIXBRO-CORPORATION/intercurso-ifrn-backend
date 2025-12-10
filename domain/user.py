from domain.abstract_domain import AbstractDomain
from dataclasses import dataclass

@dataclass
class User(AbstractDomain):

    name: str = None
    email: str = None
    cpf: int = None
    matricula: int = None
    atleta: bool = None
