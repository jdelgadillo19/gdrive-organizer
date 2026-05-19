"""Drive sync worker entrypoint (skeleton)."""

import asyncio

from kip_core.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def run() -> None:
    configure_logging()
    logger.info("drive_sync_worker_started")
    # TODO: consume Redis sync queue and invoke Drive API
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(run())
