import threading
import time
import queue

from loguru import logger

from modules.wheel.wheel import MotorControl
from core.message_queue import message_queue_manager
from core.constants import QueueNames

def wheel_thread(motor_instance):
    """
    轮子模块的处理线程
    """
    wheel_queue = message_queue_manager.get_queue(QueueNames.WHEEL)
    radar_queue = message_queue_manager.get_queue(QueueNames.RADAR)
    length = 100  # 默认距离

    while True:
        try:
            # 非阻塞地获取雷达数据
            try:
                length = radar_queue.get_nowait()
            except queue.Empty:
                pass  # 如果没有雷达数据，继续使用上一次的值

            # 阻塞地等待摇杆指令
            recv_data = wheel_queue.get(timeout=1)
            action, speed = recv_data.split('|')[0], float(recv_data.split('|')[1])

            if action == 'F':
                if length > 20:
                    motor_instance.forward(speed)
                else:
                    motor_instance.stop()
            elif action == 'B':
                motor_instance.backward(speed)
            elif action == 'L':
                motor_instance.turn_left(speed)
            elif action == 'R':
                motor_instance.turn_right(speed)
            elif action == 'S':
                motor_instance.stop()
        except queue.Empty:
            # 如果WHEEL队列超时，则停止电机
            motor_instance.stop()
        except Exception as e:
            logger.error(f"Error in wheel thread: {e}")
            motor_instance.stop()

def radar_thread(motor_instance):
    """
    雷达模块的处理线程
    """
    radar_queue = message_queue_manager.get_queue(QueueNames.RADAR)
    too_close = 0
    
    while True:
        try:
            recv_data = radar_queue.get(timeout=1)
            length = int(recv_data)
            if length <= 20:
                too_close += 1
            if too_close >= 6:
                too_close = 0
                motor_instance.stop()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error in radar thread: {e}")
        time.sleep(0.1)

def run():
    try:
        motor_instance = MotorControl(
            ENL1=27, ENL2=22,
            ENR1=23, ENR2=24,
            pwmL=17, pwmR=18
        )
        
        wheel_thread_instance = threading.Thread(target=wheel_thread, args=(motor_instance,), daemon=True)
        wheel_thread_instance.start()
        
        radar_thread_instance = threading.Thread(target=radar_thread, args=(motor_instance,), daemon=True)
        radar_thread_instance.start()

        logger.info("Wheel and Radar modules started.")
        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"Error in wheel module: {e}")
    finally:
        if 'motor_instance' in locals() and motor_instance:
            motor_instance.cleanup()
