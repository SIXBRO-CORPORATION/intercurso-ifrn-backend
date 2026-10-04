from typing import List

from core.command import Command
from domain.modality.modality import Modality


class ListModalitiesPort(Command[List[Modality]]):
    pass
