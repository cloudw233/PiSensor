import json
import threading
import time
import queue

from loguru import logger

from core.builtins.elements import HeartElements
from core.builtins.message_constructors import MessageChainD
from core.message_queue import message_queue_manager
from core.relay_server import sensor_data_handler

from modules.heart.heart import init_max30102, measure_heart_rate

def heart_thread():
    """
    心率模块的处理线程
    """
    heart_queue = message_queue_manager.get_queue('heart')
    
    while True:
        try:
            recv_data = heart_queue.get(timeout=1)
            data = MessageChainD(json.loads(recv_data))
            data.serialize()
            heart = [_ for _ in data.messages if isinstance(_, HeartElements)]
            if len(heart) != 0 and heart[0].bpm == -1:
                init_max30102()
                logger.info("[Heart]Measuring heart rate...")
                bpm = measure_heart_rate()
                logger.debug(f"[Heart]<{bpm}>")
                sensor_data_handler('heart', str(bpm))
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error in heart thread: {e}")
        time.sleep(0.1)

def run():
    try:
        heart_thread_instance = threading.Thread(target=heart_thread, daemon=True)
        heart_thread_instance.start()
        logger.info("Heart module started.")
    except Exception as e:
        logger.error(f"Error in heart module: {e}")

