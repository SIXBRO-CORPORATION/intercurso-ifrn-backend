from dataclasses import dataclass, field
from typing import List


@dataclass
class PushSendResult:

    success_count: int = 0
    failure_count: int = 0
    invalid_tokens: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.success_count + self.failure_count
