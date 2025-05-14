import asyncio
import logging
import uvicorn

import orjson as json

from fastapi import FastAPI, WebSocket
from loguru import logger

from core.builtins.message_constructors import MessageChain
from core.builtins.assigned_element import SensorElement

app = FastAPI()

sensor = SensorElement(urgent_button=False)

expired = 0

@app.websocket('/{path}')
async def websocket_endpoint(websocket: WebSocket, path: str):
    await websocket.accept()
    while True:
        data = (await websocket.receive()).get('bytes').decode('utf8')
        match path:
            case 'humiture':
                sensor.temp = json.loads(data)[0]
                sensor.humidity = json.loads(data)[1]
            case 'smbus':
                sensor.tilt = json.loads(data)['tilt']
                sensor.smoke["MQ_2"] = json.loads(data)['gas_sensors']['MQ2']
                sensor.smoke["MQ_7"] = json.loads(data)['gas_sensors']['MQ7']
                sensor.power = json.loads(data)['power']
            case 'urgent-button':
                sensor.urgent_button = True
            case 'server':
                await websocket.send_text(MessageChain([sensor]))
                sensor.urgent_button = False


async def run_delay_server():
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


        config = uvicorn.Config(app, host="localhost", port=int(10240), access_log=True, workers=2)
        server = uvicorn.Server(config)
        init_logger()
        server.run()
    except asyncio.CancelledError:
        await server.shutdown()
        raise