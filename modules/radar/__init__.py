import asyncio

import websockets

from loguru import logger
from modules.radar.radar import radar

async def run():
    await asyncio.sleep(5)
    async with websockets.connect("ws://localhost:25567/radar") as ws:
        logger.info("[Radar]Here we go!")
        await radar(ws)
