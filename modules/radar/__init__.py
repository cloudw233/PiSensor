from loguru import logger
from modules.radar.radar import run as radar
from core.message_queue import message_queue_manager
from core.constants import QueueNames
import time

def run():
    radar_queue = message_queue_manager.get_queue(QueueNames.RADAR)
    logger.info("[Radar]Here we go!")
    while True:
        distance = radar()
        if distance:
            radar_queue.put(int(distance))
        time.sleep(1)
