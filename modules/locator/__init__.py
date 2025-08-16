import asyncio
import websockets

import orjson as json

from loguru import logger
from modules.locator.locator import Locator
from core.relay_server import sensor_data_handler
import time

def run():
    _location = Locator()
    time.sleep(5)
    logger.info(f"[Location]Here we go!")
    while True:
        try:
            __location = _location.read_location()
            logger.debug(f"[Location]{__location}")
            sensor_data_handler('location', ",".join(__location))
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error in locator module: {e}")
            _location.cleanup()
            time.sleep(2)


