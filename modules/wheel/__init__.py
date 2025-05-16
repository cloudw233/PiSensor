import asyncio
import logging
import uvicorn

from fastapi import WebSocket, FastAPI
from loguru import logger

from modules.wheel.wheel import MotorControl

app = FastAPI()

motor_instance = None # 占位符，稍后由 main.py 注入

def set_motor_instance(instance):
    global motor_instance
    motor_instance = instance
    logger.info("Motor instance injected into wheel module.")


@app.websocket("/wheel")
async def wheel(websocket: WebSocket):
    await websocket.accept()
    while True:
        if motor_instance is None:
            logger.error("Motor instance not set in wheel module!")
            await websocket.close(code=1011, reason="Motor not initialized")
            return
        recv_data = await websocket.receive_text()
        action, speed = recv_data.split('|')[0], float(recv_data.split('|')[1])
        match action:
            case 'F':
                motor_instance.forward(speed)
            case 'B':
                motor_instance.backward(speed)
            case 'L':
                motor_instance.turn_left(speed)
            case 'R':
                motor_instance.turn_right(speed)
            case _:
                motor_instance.stop()


too_close = 0

@app.websocket("/radar")
async def radar(websocket: WebSocket):
    global too_close
    await websocket.accept()
    while True:
        if motor_instance is None:
            logger.error("Motor instance not set in wheel module!")
            await websocket.close(code=1011, reason="Motor not initialized")
            return
        recv_data = await websocket.receive()
        length = int(recv_data)
        if length <= 20:
            too_close += 1
        if too_close >= 6:
            too_close = 0
            motor_instance.stop()


async def run():
    try:
        if motor_instance is None:
            logger.critical("Motor instance not available when starting uvicorn for wheel module. Aborting.")
            return
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
        await server.serve()
    except asyncio.CancelledError:
        await server.shutdown()
        raise
