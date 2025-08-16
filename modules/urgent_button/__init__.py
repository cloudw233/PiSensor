import time
from gpiozero import Button
from loguru import logger
import time

from core.http_client import send_sensor_data
from main import stop_event # 导入stop_event

urgent_button = Button(16)

def run():
    logger.info("Urgent button module started.")
    while not stop_event.is_set(): # 检查stop_event
        try:
            urgent_button.wait_for_active() # 等待按钮按下
            if urgent_button.is_active: # 再次确认按钮是否真的被按下
                logger.info("Urgent button pressed.")
                send_sensor_data("urgent_button", {"value": True})
                urgent_button.wait_for_inactive() # 等待按钮释放
        except Exception as e:
            logger.error(f"Error in urgent button module: {e}")
        time.sleep(0.1) # 短暂休眠，避免CPU占用过高

