from typing import Protocol, Optional
from src.core.schemas import RawEvent


class MessageQueue(Protocol):
    def push(self, event: RawEvent) -> None: ...
    def pop(self) -> Optional[RawEvent]: ...
