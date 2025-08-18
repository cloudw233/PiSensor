import time
import orjson as json

from loguru import logger
from modules.smbus.smbus import IntegratedSensorHub
from core.message_queue import message_queue_manager
from core.constants import QueueNames

smbus_queue = message_queue_manager.get_queue(QueueNames.SMBUS)

def run():
    __hub = IntegratedSensorHub()
    time.sleep(5)
    while True:
        try:
            __data = __hub.read_all()
            logger.debug(f"[SensorHub]{__data}")
            smbus_queue.put(__data)
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error in smbus module: {e}")
            __hub.close()
            time.sleep(2)

