from loguru import logger
from modules.radar.radar import run as radar
from core.message_queue import message_queue_manager
from core.constants import QueueNames
import time

def run():
    logger.info("[Radar]Here we go!")
    while True:
        radar()
        time.sleep(0.1)

