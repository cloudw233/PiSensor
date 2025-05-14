import asyncio
import websockets

from loguru import logger
from .radar import radar

async def run():
    async with websockets.connect("ws://localhost:10240/radar") as ws:
        logger.info("[Radar]Here we go!")
        await radar(ws)
        await asyncio.sleep(2)
