from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from domain.messaging.push_send_result import PushSendResult


class PushSenderPort(ABC):

    @abstractmethod
    async def send(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> PushSendResult:
        pass

    @abstractmethod
    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> None:
        pass
