import asyncio

import orjson as json

from fastapi import FastAPI, WebSocket
from core.builtins.message_constructors import MessageChain
from core.builtins.assigned_element import SensorElement

app = FastAPI()

sensor = SensorElement()

@app.websocket('/{path}')
async def websocket_endpoint(websocket: WebSocket, path: str):
    await websocket.accept()
    while True:
        data = (await websocket.receive()).get('bytes').decode('utf8')
        try:
            if path != 'sensor':
                match path:
                    case 'humiture':
                        sensor.humidity = json.loads(data)

        except asyncio.CancelledError:
            raise