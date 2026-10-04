from typing import List

from core.command import Command
from domain.match.match import Match


class ListPublicMatchesPort(Command[List[Match]]):
    pass