from typing import Protocol, Optional
from src.core.schemas import RawEvent


class MessageQueue(Protocol):
    async def pop(self) -> Optional[RawEvent]: ...
    async def push(self, event: RawEvent) -> None: ...
