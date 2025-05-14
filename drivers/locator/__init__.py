import asyncio
import websockets

from loguru import logger
from .locator import Locator

async def run():
    _location = Locator()
    while True:
        try:
            async with websockets.connect("ws://localhost:10240/location") as ws:
                __location = _location.read_location()
                logger.debug(f"[Location]{__location}")
                await ws.send(__location)
                await asyncio.sleep(2)
        except SystemExit:
            _location.cleanup()
            break
        except Exception:
            logger.exception("[Location]<UNK>")


