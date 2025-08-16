import threading
import time
import json

from loguru import logger
from modules.humiture.humiture import get_humiture
from core.message_queue import message_queue_manager
from core.http_client import send_sensor_data

def run():
    # 等待5秒后开始运行
    time.sleep(5)
    while True:
        try:
            # 获取温湿度数据
            temperature, humidity = get_humiture()
            logger.debug(f"[Humiture] Temperature: {temperature}, Humidity: {humidity}")
            
            # 通过队列发送数据到中继服务器
            send_sensor_data('humiture', {'temperature': temperature, 'humidity': humidity})
            
            # 每2秒发送一次数据
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error in humiture module: {e}")
            time.sleep(2)

