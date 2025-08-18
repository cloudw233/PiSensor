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
    consecutive_errors = 0
    max_consecutive_errors = 10

    time.sleep(5)
    while True:
        try:
            # 获取温湿度数据
            result = get_humiture()
            if result is not None:
                temperature, humidity = result
                logger.info(f"[Humiture] Temperature: {temperature}, Humidity: {humidity}")
                
                # 通过队列发送数据到中继服务器
                humiture_queue.put({'temperature': temperature, 'humidity': humidity})
                consecutive_errors = 0  # 重置错误计数
            else:
                logger.warning("[Humiture] Failed to get sensor data, using default values")
                humiture_queue.put({'temperature': 25.0, 'humidity': 50.0})
                consecutive_errors += 1
            
            # 每2秒发送一次数据
            time.sleep(2)
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in humiture module: {e}")
            
            # 如果连续错误太多，增加等待时间
            if consecutive_errors >= max_consecutive_errors:
                logger.warning(f"[Humiture] Too many consecutive errors ({consecutive_errors}), extending sleep time")
                time.sleep(10)
                consecutive_errors = 0
            else:
                time.sleep(2)

