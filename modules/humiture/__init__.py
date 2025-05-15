import asyncio
import websockets

import orjson as json

from loguru import logger
from modules.humiture.humiture import get_humiture

async def run():
    await asyncio.sleep(5)
    while True:
        try:
            async with websockets.connect("ws://localhost:10240/humiture") as ws:
                __humiture = get_humiture()
                logger.debug(f"[Humiture]{__humiture}")
                await ws.send(json.dumps(__humiture))
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            raise

