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
        'R': (3072,1024),
        'L': (0,1024),
        'F': (1024,0),
        'B': (1024,3072)
    }
    mapping_max = {
        'R': (4092,3072),
        'L': (1024,3072),
        'F': (3072,1024),
        'B': (3072,4092)
    }
    min_val_x, min_val_y = mapping_min[direction]
    max_val_x, max_val_y = mapping_max[direction]
    value_x, value_y, _ = value
    x_normalized = abs(value_x - min_val_x) / (max_val_x - min_val_x) if (max_val_x - min_val_x) != 0 else 0
    y_normalized = abs(value_y - min_val_y) / (max_val_y - min_val_y) if (max_val_y - min_val_y) != 0 else 0
    speed = hypot(x_normalized, y_normalized)
    return round(min(1.0, max(0.0, speed)), 3)

def run():
    joystick = MCP3208_Joystick()
    wheel_queue = message_queue_manager.get_queue(QueueNames.WHEEL)
    logger.info("Rocker module started.")
    try:
        while True:
            value = joystick.read_joystick()
            logger.debug(f"Joystick value: {value}")
            if value[0] > 3072 and value[1] > 1024 and value[1] < 3072:
                wheel_queue.put(f'R|{calc_speed(value, "R"):.3f}')
            elif value[0] < 1024 and value[1] > 1024 and value[1] < 3072:
                wheel_queue.put(f'L|{calc_speed(value, "L"):.3f}')
            elif value[0] > 1024 and value[0] < 3072 and value[1] < 1024:
                wheel_queue.put(f'F|{calc_speed(value, "F"):.3f}')
            elif value[0] > 1024 and value[0] < 3072 and value[1] > 3072:
                wheel_queue.put(f'B|{calc_speed(value, "B"):.3f}')
            else:
                wheel_queue.put('S|0')
            time.sleep(0.01)
    except Exception as e:
        logger.error(f"Error in rocker module: {e}")
    finally:
        if 'joystick' in locals() and joystick:
            joystick.close()

