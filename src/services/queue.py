import redis
import logging
from redis import Redis
from pydantic import ValidationError
from redis.exceptions import RedisError
from src.config import settings
from src.interfaces import MessageQueue
from src.core.schemas import RawEvent

logger = logging.getLogger(__name__)


class RedisQueue(MessageQueue):
    def __init__(self):
        self.client = Redis.from_url(settings.REDIS_URL)

    def push(self, event: RawEvent) -> None:
        self.client.lpush(settings.QUEUE_NAME, event.model_dump_json())
    
    def pop(self) -> RawEvent | None:
        
        try:
            # get from queue with block so wait sometime until something arrives
            result = self.client.blpop(settings.QUEUE_NAME, timeout=1)

            if not result:
                return None

            raw_data = result[1]

            return RawEvent.model_validate_json(raw_data)
        
        except ValidationError as e:
            logger.error(f" Invalid Schema: {e}")
            return None
        except RedisError as e:
            logger.error(f" Redis Error: {e})")
            return None
        except Exception as e:
            logger.error(f" Error: {e}")
            return None