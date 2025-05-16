import asyncio
import logging
import uvicorn
import websockets

import orjson as json

from fastapi import FastAPI, WebSocket
from loguru import logger

from core.builtins.elements import StepperMotorElements, HeartElements, MachineryElements
from core.builtins.message_constructors import MessageChain, MessageChainD
from core.builtins.assigned_element import SensorElement, AccountElement

from config import config

app = FastAPI()

sensor = SensorElement(temp=0.0,
    humidity=0.0,
    power=30.0,
    urgent_button=False,
    tilt=False,
    heart_data=0,
    smoke={"MQ_2": False, "MQ_7": False},
    seat=0,
    gps='0,0'
    )
account = AccountElement(
    username=config('username'),
    action='data',
    key=config('key'),
)

@app.websocket('/server')
async def websocket_server(websocket: WebSocket):
    await websocket.accept()
    async with websockets.connect('ws://localhost:25565/heart') as heart, \
            websockets.connect('ws://localhost:25566/step-motor') as step, \
            websockets.connect('ws://localhost:25567/wheel') as wheel:
        while True:
            data = (await websocket.receive()).get('bytes').decode('utf8')
            await websocket.send_text(MessageChain([account, sensor]))
            sensor.urgent_button = False
            parsed_msg = MessageChainD(json.loads(data))
            parsed_msg.serialize()
            step_e = [_ for _ in parsed_msg.messages if isinstance(_, StepperMotorElements)]
            heart_e = [_ for _ in parsed_msg.messages if isinstance(_, HeartElements)]
            wheel_e = [_ for _ in parsed_msg.messages if isinstance(_, MachineryElements)]
            for e in [step_e, heart_e, wheel_e]:
                if len(e) > 0:
                    if e == step_e:
                        await step.send(json.dumps(MessageChain([account, e[0]]).deserialize()))
                    elif e == heart_e:
                        await heart.send(json.dumps(MessageChain([account, e[0]]).deserialize()))
                    elif e == wheel_e:
                        await wheel.send(json.dumps(MessageChain([account, e[0]]).deserialize()))



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
            case 'location':
                sensor.gps = data


async def run_relay_server():
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
        await server.serve()
    except asyncio.CancelledError:
        await server.shutdown()
        raise