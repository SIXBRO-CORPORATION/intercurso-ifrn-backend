from datetime import date
from typing import Optional
from domain.abstract_domain import AbstractDomain
from domain.enums.gender import Gender
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
    gender: Optional[Gender] = None
    tipo_usuario: Optional[str] = None
    campus: Optional[str] = None
    curso: Optional[str] = None
    turno: Optional[str] = None
    email_classroom: Optional[str] = None
    photo: Optional[str] = None
    birth_date: Optional[date] = None

    @classmethod
    def from_suap_dict(
        cls, identificacao: dict, dados_aluno: Optional[dict] = None
    ) -> "User":

        tipo_usuario = identificacao.get("tipo_usuario")

        vinculo = (dados_aluno or {}).get("vinculo") or {}
        curso = vinculo.get("curso")
        turno = vinculo.get("turno")

        sexo = identificacao.get("sexo")
        gender = Gender(sexo) if sexo in {g.value for g in Gender} else None

        birth_date_str = identificacao.get("data_de_nascimento")
        birth_date = None
        if birth_date_str:
            try:
                birth_date = date.fromisoformat(birth_date_str)
            except ValueError:
                birth_date = None

        matricula = identificacao.get("identificacao") or (
            dados_aluno.get("matricula") if dados_aluno else None
        )

        return cls(
            matricula=str(matricula) if matricula else None,
            name=identificacao.get("nome_usual") or identificacao.get("nome"),
            email=identificacao.get("email_preferencial")
            or identificacao.get("email"),
            email_classroom=identificacao.get("email_google_classroom"),
            cpf=str(identificacao.get("cpf", "")).replace(".", "").replace("-", ""),
            tipo_usuario=tipo_usuario,
            campus=identificacao.get("campus"),
            curso=curso,
            turno=turno,
            gender=gender,
            photo=identificacao.get("foto"),
            birth_date=birth_date,
        )
