import websockets

from loguru import logger
from modules.radar.radar import radar

async def run():
    async with websockets.connect("ws://localhost:10240/radar") as ws:
        logger.info("[Radar]Here we go!")
        await radar(ws)
