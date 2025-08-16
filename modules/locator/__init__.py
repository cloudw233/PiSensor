import orjson as json

import time

from loguru import logger
from modules.locator.locator import Locator
from core.http_client import send_sensor_data

def run():
    _location = Locator()
    time.sleep(5)
    logger.info(f"[Location]Here we go!")
    while True:
        try:
            __location = _location.read_location()
            logger.debug(f"[Location]{__location}")
            send_sensor_data('locator', ",".join(map(str, __location)))
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error in locator module: {e}")
            _location.cleanup()
            time.sleep(2)


