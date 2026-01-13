from enum import Enum


class EventType(Enum):
    MATCH_STARTED = "Partida iniciada"
    MATCH_END = "Partida finalizada"
    PERIOD_START = "Período iniciado"
    PERIOD_END = "Período finalizado"
    GOAL = "Gol"
    POINT = "Ponto"
    CARD_YELLOW = "Cartão amerelo"
    CARD_RED = "Cartão vermelho"
    EXPULSION = "Expulsão"