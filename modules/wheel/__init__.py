import asyncio
import logging
import uvicorn

from fastapi import WebSocket, FastAPI
from loguru import logger

from modules.wheel.wheel import MotorControl

app = FastAPI()

motor = MotorControl(
    ENL1=27, ENL2=22,  # 左电机方向控制引脚
    ENR1=23, ENR2=24,  # 右电机方向控制引脚
    pwmL=17, pwmR=18  # PWM速度控制引脚
)


@app.websocket("/wheel")
async def wheel(websocket: WebSocket):
    await websocket.accept()
    while True:
        recv_data = (await websocket.receive()).get('bytes').decode('utf8')
        action, speed = recv_data.split('|')[0], float(recv_data.split('|')[1])
        match action:
            case 'F':
                motor.forward(speed)
            case 'B':
                motor.backward(speed)
            case 'L':
                motor.turn_left(speed)
            case 'R':
                motor.turn_right(speed)
            case _:
                motor.stop()


too_close = 0

@app.websocket("/radar")
async def radar(websocket: WebSocket):
    global too_close
    await websocket.accept()
    while True:
        recv_data = (await websocket.receive()).get('bytes').decode('utf8')
        length = int(recv_data)
        if length <= 20:
            too_close += 1
        if too_close >= 6:
            too_close = 0
            motor.stop()


async def run():
    try:
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                logger_opt = logger.opt(depth=6, exception=record.exc_info)
                logger_opt.log(record.levelno, record.getMessage())

        def init_logger():
            LOGGER_NAMES = ("uvicorn", "uvicorn.access",)
            for logger_name in LOGGER_NAMES:
                logging_logger = logging.getLogger(logger_name)
                logging_logger.handlers = [InterceptHandler()]

        config = uvicorn.Config(app, host="localhost", port=int(25567), access_log=True, workers=2)
        server = uvicorn.Server(config)
        init_logger()
        server.run()
    except asyncio.CancelledError:
        await server.shutdown()
        raise
