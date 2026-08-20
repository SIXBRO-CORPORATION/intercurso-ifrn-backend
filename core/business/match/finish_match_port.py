from core.command import Command
from domain.match.match import Match


class FinishMatchPort(Command[Match]):
    pass
