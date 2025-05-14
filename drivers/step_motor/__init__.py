import orjson as json
import logging
import uvicorn

from fastapi import FastAPI, WebSocket
from loguru import logger

from core.builtins.assigned_element import HeartElement
from core.builtins.elements import HeartElements
from core.builtins.message_constructors import MessageChainD, MessageChain

from .step_motor import StepperMotor

app = FastAPI()

@app.websocket("/--heart")
async def heart(websocket: WebSocket):
    await websocket.accept()
    while True:
        recv_data = await websocket.receive_text()
        data = MessageChainD(json.loads(recv_data))
        data.serialize()
        heart = [_ for _ in data.messages if isinstance(_, HeartElements)]
        if len(heart) != 0 and heart[0].bpm == -1:
            init_max30102()
            logger.info("[Heart]Measuring heart rate...")
            bpm = measure_heart_rate()
            logger.debug(f"[Heart]<{heart[0].bpm}>")
            await websocket.send_text(MessageChain(HeartElement(bpm)))

async def run():
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            logger_opt = logger.opt(depth=6, exception=record.exc_info)
            logger_opt.log(record.levelno, record.getMessage())


    def init_logger():
        LOGGER_NAMES = ("uvicorn", "uvicorn.access",)
        for logger_name in LOGGER_NAMES:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = [InterceptHandler()]


    config = uvicorn.Config(app, host="0.0.0.0", port=int(25565), access_log=True, workers=2)
    server = uvicorn.Server(config)
    init_logger()
    server.run()

