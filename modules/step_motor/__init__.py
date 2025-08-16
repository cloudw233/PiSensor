import json
import threading
import time
import queue

from loguru import logger

from core.builtins.elements import StepperMotorElements
from core.builtins.message_constructors import MessageChainD
from core.message_queue import message_queue_manager

from modules.step_motor.step_motor import StepperMotor

def stepper_motor_thread():
    """
    步进电机模块的处理线程
    """
    step_motor_queue = message_queue_manager.get_queue('step_motor')
    
    while True:
        try:
            recv_data = step_motor_queue.get(timeout=1)
            data = MessageChainD(json.loads(recv_data))
            data.serialize()
            motor = [_ for _ in data.messages if isinstance(_, StepperMotorElements)]
            if len(motor) != 0:
                _step_motor = StepperMotor(*motor[0].pin)
                _step_motor.rotate(motor[0].step)
                _step_motor.release()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error in stepper motor thread: {e}")
        time.sleep(0.1)

def run():
    try:
        stepper_motor_thread_instance = threading.Thread(target=stepper_motor_thread, daemon=True)
        stepper_motor_thread_instance.start()
        logger.info("Stepper motor module started.")
    except Exception as e:
        logger.error(f"Error in step motor module: {e}")

