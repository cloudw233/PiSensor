import asyncio
import websockets

from loguru import logger
from modules.smbus.smbus import IntegratedSensorHub


async def run():
    __hub = IntegratedSensorHub()
    while True:
        try:
            async with websockets.connect("ws://localhost:10240/humiture") as ws:
                __data = __hub.read_all()
                logger.debug(f"[SensorHub]{__data}")
                await ws.send(__data)
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            __hub.close()
            raise

