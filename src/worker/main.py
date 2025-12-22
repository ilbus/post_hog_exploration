import time
import logging
from sqlalchemy.exc import SQLAlchemyError
from src.services.queue import RedisQueue
from src.services.enrichment import enrich_event
from src.db.session import SessionLocal
from src.db.models import EventModel
from src.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")


def run_worker():
    queue = RedisQueue()
    logger.info("Worker started. Listening...")

    batch_buffer = []
    last_flush_time = time.time()

    while True:
        try:
            # pop has timeout of 1s
            event = queue.pop()
            if event:
                try:
                    enriched = enrich_event(event)

                    # prepare db object without save/commit
                    db_event = EventModel(
                        user_id=enriched.user_id,
                        session_id=enriched.session_id,
                        semantic_label=enriched.semantic_label,
                        raw_payload=enriched.original_event.model_dump_json(),
                        created_at=enriched.original_event.timestamp,
                    )
                    batch_buffer.append(db_event)
                except Exception as e:
                    logger.error(f"Error enriching event: {e}")
                    continue

            # check flush condition
            current_time = time.time()
            is_batch_full = len(batch_buffer) >= settings.BATCH_SIZE
            is_time_elapsed = (
                current_time - last_flush_time
            ) >= settings.FLUSH_INTERVAL

            if batch_buffer and (is_batch_full or is_time_elapsed):
                try:
                    with SessionLocal() as db:
                        # bulk insert
                        db.add_all(batch_buffer)

                        db.commit()
                        logger.info(f" Flushed batch of {len(batch_buffer)} events")

                except SQLAlchemyError as e:
                    logger.error(f"Database Error: {e}")

                    try:
                        pipeline = queue.client.pipeline()
                        for item in batch_buffer:
                            pipeline.lpush(settings.DLQ_NAME, item.raw_payload)
                        pipeline.execute()
                        logger.info(
                            f"Moved {len(batch_buffer)} events to DLQ: {settings.DLQ_NAME}"
                        )

                    except Exception as e:
                        logger.error(f"Error moving events to DLQ: {e}")

                finally:
                    # reset buffer and flush time
                    batch_buffer = []
                    last_flush_time = current_time

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_worker()
