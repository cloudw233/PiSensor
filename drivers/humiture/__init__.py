import asyncio
import websockets

from loguru import logger
from .humiture import get_humiture

async def run():
    while True:
        try:
            async with websockets.connect("ws://localhost:10240/humiture") as ws:
                __humiture = get_humiture()
                logger.debug(f"[Humiture]{__humiture}")
                await ws.send(__humiture)
                await asyncio.sleep(2)
        except Exception:
            logger.exception("[Humiture]<UNK>")

