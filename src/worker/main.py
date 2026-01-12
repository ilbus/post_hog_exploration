import asyncio
import logging
import signal
from sqlalchemy.exc import SQLAlchemyError
from src.services.queue import RedisQueue
from src.services.enrichment import enrich_event
from src.db.session import AsyncSessionLocal
from src.db.models import EventModel
from src.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")


class GracefulExit(SystemExit):
    code = 1


def _handle_exit(signum, frame):
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    raise GracefulExit()


async def flush_batch(batch_buffer, queue):
    if not batch_buffer:
        return

    try:
        async with AsyncSessionLocal() as db:
            db.add_all(batch_buffer)
            await db.commit()
            logger.info(f"Flushed batch of {len(batch_buffer)} events")
    except SQLAlchemyError as e:
        logger.error(f"Database Error during flush: {e}")
        try:
            async with queue.client.pipeline() as pipeline:
                for item in batch_buffer:
                    pipeline.lpush(settings.DLQ_NAME, item.raw_payload)
                await pipeline.execute()
            logger.info(
                f"Moved {len(batch_buffer)} events to DLQ: {settings.DLQ_NAME}"
            )
        except Exception as e_dlq:
            logger.error(f"Error moving events to DLQ during flush: {e_dlq}")
    except Exception as e:
        logger.error(f"Unexpected error during flush: {e}")


async def run_worker():
    # Register signal handlers
    signal.signal(signal.SIGTERM, _handle_exit)
    signal.signal(signal.SIGINT, _handle_exit)

    queue = RedisQueue()
    logger.info("Worker started. Listening...")

    batch_buffer = []
    last_flush_time = asyncio.get_running_loop().time()
    
    running = True

    while running:
        try:
            try:
                # pop has timeout of 1s
                event = await queue.pop()
            except GracefulExit:
                running = False
                break
            except Exception as e:
                 logger.error(f"Error popping from queue: {e}")
                 await asyncio.sleep(1)
                 continue

            if event:
                try:
                    enriched = enrich_event(event)
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
                    # Send raw event back to DLQ if possible
                    try:
                        await queue.push_raw(settings.DLQ_NAME, event.model_dump_json())
                        logger.info(f"Moved failed enrichment event to DLQ")
                    except Exception as dlq_ex:
                        logger.error(f"Failed to push to DLQ: {dlq_ex}")
                    continue

            # check flush condition
            current_time = asyncio.get_running_loop().time()
            is_batch_full = len(batch_buffer) >= settings.BATCH_SIZE
            is_time_elapsed = (
                current_time - last_flush_time
            ) >= settings.FLUSH_INTERVAL

            if batch_buffer and (is_batch_full or is_time_elapsed):
                await flush_batch(batch_buffer, queue)
                batch_buffer = []
                last_flush_time = current_time
            
            # Optional wait if empty
            if not event and running:
                 await asyncio.sleep(0.1)

        except GracefulExit:
            running = False
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
            await asyncio.sleep(1)
    
    # Final cleanup
    logger.info("Worker loop finished. Flushing remaining buffer...")
    if batch_buffer:
        await flush_batch(batch_buffer, queue)
    
    await queue.close()
    logger.info("Worker shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except (KeyboardInterrupt, GracefulExit):
        pass
    except Exception as e:
        logger.error(f"Critical worker error: {e}")
