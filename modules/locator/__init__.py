import asyncio
import websockets

import orjson as json

from loguru import logger
from modules.locator.locator import Locator

async def run():
    _location = Locator()
    await asyncio.sleep(5)
    logger.info(f"[Location]Here we go!")
    while True:
        try:
            async with websockets.connect("ws://localhost:10240/location") as ws:
                __location = _location.read_location()
                logger.debug(f"[Location]{__location}")
                await ws.send(','.join(__location))
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            _location.cleanup()
            raise


