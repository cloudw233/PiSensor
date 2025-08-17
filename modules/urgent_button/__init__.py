import time
from gpiozero import Button
from loguru import logger

from core.http_client import send_sensor_data

urgent_button = Button(16)

def run():
    logger.info("Urgent button module started.")
    while True:
        try:
            if urgent_button.is_active:
                logger.info("Urgent button pressed.")
                send_sensor_data("urgent_button", {"value": True})
            else:
                send_sensor_data("urgent_button", {"value": False})
            time.sleep(0.01)  # Debounce
        except Exception as e:
            logger.error(f"Error in urgent button module: {e}")

