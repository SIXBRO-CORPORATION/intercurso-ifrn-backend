from enum import Enum


class SeasonStatus(Enum):
    DRAFT = "Rascunho"
    REGISTRATION_OPEN = "Inscrições abertas"
    REGISTRATION_CLOSED = "Inscrições fechadas"
    IN_PROGRESS = "Em progresso"
    FINISHED = "Finalizada"