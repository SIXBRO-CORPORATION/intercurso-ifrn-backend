from enum import Enum


class MatchStatus(Enum):
    SCHEDULED = "Agendada"
    IN_PROGRESS = "Em progresso"
    FINISHED = "Finalizada"