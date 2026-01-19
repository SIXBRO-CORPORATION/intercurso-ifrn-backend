from enum import Enum


class TeamStatus(Enum):
    DRAFT = "Rascunho"
    SUBMITTED = "Aprovação Pendente"
    APPROVED = "Aprovado"
    REJECTED = "Rejeitado"
