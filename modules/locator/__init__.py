import orjson as json

import time

from loguru import logger
from modules.locator.locator import Locator
from core.message_queue import message_queue_manager
from core.constants import QueueNames


def run():
    locator_queue = message_queue_manager.get_queue(QueueNames.LOCATOR)
    _location = Locator()
    time.sleep(5)
    logger.info(f"[Location]Here we go!")
    while True:
        try:
            __location = _location.read_location()
            logger.debug(f"[Location]{__location}")
            locator_queue.put(__location)
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error in locator module: {e}")
            _location.cleanup()
            time.sleep(2)


