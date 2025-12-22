import asyncio
import logging
from sqlalchemy.exc import SQLAlchemyError
from src.services.queue import RedisQueue
from src.services.enrichment import enrich_event
from src.db.session import AsyncSessionLocal
from src.db.models import EventModel
from src.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")


async def run_worker():
    queue = RedisQueue()
    logger.info("Worker started. Listening...")

    batch_buffer = []
    last_flush_time = asyncio.get_running_loop().time()

    while True:
        try:
            # pop has timeout of 1s
            event = await queue.pop()
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
            current_time = asyncio.get_running_loop().time()
            is_batch_full = len(batch_buffer) >= settings.BATCH_SIZE
            is_time_elapsed = (
                current_time - last_flush_time
            ) >= settings.FLUSH_INTERVAL

            if batch_buffer and (is_batch_full or is_time_elapsed):
                try:
                    async with AsyncSessionLocal() as db:
                        # bulk insert
                        db.add_all(batch_buffer)

                        await db.commit()
                        logger.info(f" Flushed batch of {len(batch_buffer)} events")

                except SQLAlchemyError as e:
                    logger.error(f"Database Error: {e}")

                    try:
                        async with queue.client.pipeline() as pipeline:
                            for item in batch_buffer:
                                pipeline.lpush(settings.DLQ_NAME, item.raw_payload)
                            await pipeline.execute()
                        logger.info(
                            f"Moved {len(batch_buffer)} events to DLQ: {settings.DLQ_NAME}"
                        )

                    except Exception as e:
                        logger.error(f"Error moving events to DLQ: {e}")

                finally:
                    # reset buffer and flush time
                    batch_buffer = []
                    last_flush_time = current_time

            # Optional: Short sleep to prevent tight loop CPU hogging if queue is empty
            if not event:
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped manually")
