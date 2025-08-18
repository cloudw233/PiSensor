import threading
import time
import json

from loguru import logger
from modules.humiture.humiture import get_humiture
from core.message_queue import message_queue_manager
from core.constants import QueueNames

def run():
    # 等待5秒后开始运行
    humiture_queue = message_queue_manager.get_queue(QueueNames.HUMITURE)

    time.sleep(5)
    while True:
        try:
            # 获取温湿度数据
            temperature, humidity = get_humiture()
            logger.info(f"[Humiture] Temperature: {temperature}, Humidity: {humidity}")
            
            # 通过队列发送数据到中继服务器
            humiture_queue.put({'temperature': temperature, 'humidity': humidity})
            
            # 每2秒发送一次数据
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in humiture module: {e}")
            time.sleep(1)

