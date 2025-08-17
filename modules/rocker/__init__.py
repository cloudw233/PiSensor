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
    """
    根据摇杆在一个轴上的偏移量计算速度。
    偏移量越大，速度越高。

    :param value: 摇杆读数 (x, y, button_state)
    :param direction: 移动方向
    :return: 速度值 (0.0 到 1.0)
    """
    x, y, _ = value
    center = 2048
    # 摇杆值范围 0-4095, 中心点 2048
    # 死区范围 1024-3072, 对应中心偏移量 1024
    dead_zone_offset = 1024
    # 最大偏移量 2047 (例如 4095 - 2048)
    max_offset = 2047

    offset = 0
    if direction in ('R', 'L'):
        offset = abs(x - center)
    elif direction in ('F', 'B'):
        offset = abs(y - center)

    if offset <= dead_zone_offset:
        return 0.0

    # 将超出死区部分的偏移量映射到速度值
    speed = (offset - dead_zone_offset) / (max_offset - dead_zone_offset)

    # 确保速度不超过1.0
    return min(speed, 1.0)


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

