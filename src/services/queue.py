import redis
from src.config import settings
from src.interfaces import MessageQueue
from src.core.schemas import RawEvent

class RedisQueue(MessageQueue):
    def __init__(self):
        self.client = redis.Redis.from_url(settings.REDIS_URL)

    def push(self, event: RawEvent) -> None:
        self.client.lpush(settings.QUEUE_NAME, event.model_dump_json())
    
    def pop(self) -> RawEvent | None:
        # get from queue with block so wait sometime until something arrives
        result = self.client.blpop(settings.QUEUE_NAME, timeout=1)
        if result:
            return RawEvent.model_validate_json(result[1])
        return None