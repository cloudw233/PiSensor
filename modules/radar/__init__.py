from loguru import logger
from core.message_queue import message_queue_manager
from core.constants import QueueNames
import time
from modules.radar.radar import run as radar_main_run
from loguru import logger

def run():
    radar_queue = message_queue_manager.get_queue(QueueNames.RADAR)
    logger.info("[Radar]Here we go!")
    radar_main_run()
