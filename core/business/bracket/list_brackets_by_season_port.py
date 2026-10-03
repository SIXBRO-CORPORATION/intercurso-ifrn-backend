from typing import List

from core.command import Command
from domain.bracket.bracket import Bracket


class ListBracketsBySeasonPort(Command[List[Bracket]]):
    pass
