import asyncio
from typing import Tuple, Literal
from numpy import hypot

import websockets

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

async def run():
    try:
        async with websockets.connect('ws://localhost:25567/rocker') as ws:
            joystick = MCP3208_Joystick()
            while True:
                value = joystick.read_joystick()
                if 1023 >= value[0] >= 768 >= value[1] >= 256:
                    await ws.send('R'.join(f'|{calc_speed(value, "R"):.3f}'))
                elif 0 <= value[0] <= 256 <= value[1] <= 768:
                    await ws.send('L'.join(f'|{calc_speed(value, "L"):.3f}'))
                elif 768 >= value[0] >= 256 >= value[1] >= 0:
                    await ws.send('F'.join(f'|{calc_speed(value, "F"):.3f}'))
                elif 256 <= value[0] <= 768 <= value[1] <= 1023:
                    await ws.send('B'.join(f'|{calc_speed(value, "B"):.3f}'))
                else:
                    await ws.send('S'.join('|0'))
    except asyncio.CancelledError:
        joystick.close()
        raise

