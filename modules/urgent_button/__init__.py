import time
from gpiozero import Button
from loguru import logger

from core.message_queue import message_queue_manager
from core.constants import QueueNames

urgent_button = Button(16)


def run():
    urgent_button_queue = message_queue_manager.get_queue(QueueNames.URGENT_BUTTON)
    logger.info("Urgent button module started.")
    while True:
        try:
            if not urgent_button.is_active:
                logger.info("Urgent button pressed.")
                urgent_button_queue.put({"value": True})
                time.sleep(0.5)  # Debounce
            else:
                urgent_button_queue.put({"value": False})
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in urgent button module: {e}")

