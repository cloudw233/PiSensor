import time
from typing import Tuple, Literal
from numpy import hypot

from loguru import logger

from core.message_queue import message_queue_manager
from core.constants import QueueNames
from modules.rocker.rocker import MCP3208_Joystick

def calc_speed(
        value: Tuple[float, float, bool],
        direction: Literal['R', 'L', 'F', 'B']
) -> float:
    mapping_min = {
        'R': (768,256),
        'L': (0,256),
        'F': (256,0),
        'B': (256,768)
    }
    mapping_max = {
        'R': (1023,768),
        'L': (256,768),
        'F': (768,256),
        'B': (768,1023)
    }
    min_val_x, min_val_y = mapping_min[direction]
    max_val_x, max_val_y = mapping_max[direction]
    value_x, value_y, _ = value
    return hypot((value_x-min_val_x)/(max_val_x-min_val_x), (value_y-min_val_y)/(max_val_y-min_val_y))

def run():
    joystick = MCP3208_Joystick()
    wheel_queue = message_queue_manager.get_queue(QueueNames.WHEEL)
    logger.info("Rocker module started.")
    try:
        while True:
            value = joystick.read_joystick()
            logger.debug(f"Joystick value: {value}")
            if 1023 >= value[0] >= 768 >= value[1] >= 256:
                wheel_queue.put(f'R|{calc_speed(value, "R"):.3f}')
            elif 0 <= value[0] <= 256 <= value[1] <= 768:
                wheel_queue.put(f'L|{calc_speed(value, "L"):.3f}')
            elif 768 >= value[0] >= 256 >= value[1] >= 0:
                wheel_queue.put(f'F|{calc_speed(value, "F"):.3f}')
            elif 256 <= value[0] <= 768 <= value[1] <= 1023:
                wheel_queue.put(f'B|{calc_speed(value, "B"):.3f}')
            else:
                wheel_queue.put('S|0')
            time.sleep(0.1)
    except Exception as e:
        logger.error(f"Error in rocker module: {e}")
    finally:
        joystick.close()

