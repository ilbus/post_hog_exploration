import time
import logging
from src.services.queue import RedisQueue
from src.services.enrichment import enrich_event
from src.db.session import SessionLocal
from src.db.models import EventModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

def run_worker():
    logger.info("Worker started. Listening...")
    queue = RedisQueue()

    while True:
        try:
            event = queue.pop()
            if event:
                enriched = enrich_event(event)
                with SessionLocal() as db:
                    db_event = EventModel(
                        user_id=enriched.user_id,
                        session_id=enriched.session_id,
                        semantic_label=enriched.semantic_label,
                        raw_payload=enriched.original_event.model_dump_json(),
                        created_at=enriched.original_event.timestamp
                    )
                    db.add(db_event)
                    db.commit()
                    logger.info(f" Processed: {enriched.semantic_label}")
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_worker()        
