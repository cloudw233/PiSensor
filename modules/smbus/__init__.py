import time
import orjson as json

from loguru import logger
from modules.smbus.smbus import IntegratedSensorHub
from core.relay_server import sensor_data_handler

def run():
    __hub = IntegratedSensorHub()
    time.sleep(5)
    while True:
        try:
            __data = __hub.read_all()
            logger.debug(f"[SensorHub]{__data}")
            sensor_data_handler('smbus', json.dumps(__data))
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error in smbus module: {e}")
            __hub.close()
            time.sleep(2)

