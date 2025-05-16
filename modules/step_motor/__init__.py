import asyncio

import orjson as json
import logging
import uvicorn

from fastapi import FastAPI, WebSocket
from loguru import logger

from core.builtins.elements import StepperMotorElements
from core.builtins.message_constructors import MessageChainD, MessageChain

from modules.step_motor.step_motor import StepperMotor

app = FastAPI()

@app.websocket("/step-motor")
async def stepper_motor(websocket: WebSocket):
    await websocket.accept()
    while True:
        recv_data = await websocket.receive_text()
        data = MessageChainD(json.loads(recv_data))
        data.serialize()
        motor = [_ for _ in data.messages if isinstance(_, StepperMotorElements)]
        if len(motor) != 0:
            _step_motor = StepperMotor(*motor[0].pin)
            _step_motor.rotate(motor[0].step)
            _step_motor.release()

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


        config = uvicorn.Config(app, host="localhost", port=int(25566), access_log=True, workers=2)
        server = uvicorn.Server(config)
        init_logger()
        await server.serve()
    except asyncio.CancelledError:
        await server.shutdown()
        raise

