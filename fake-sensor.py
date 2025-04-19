
import websockets
import asyncio
import orjson as json


async def main():
    uri = "ws://127.0.0.1:55433/sensor"
    async with websockets.connect(uri) as websocket:
        while True:
            # 每10秒执行一次逻辑
            await asyncio.sleep(10)

            # 发送数据
            data = {"message": "ping"}
            await websocket.send(json.dumps(data))

            # 接收数据
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                received_data = json.loads(message)
                if "heartdata" in received_data:
                    # 如果包含 "heartdata"，发送 {"bpm": 70}
                    response = {"bpm": 70}
                    await websocket.send(str(json.dumps(response)), text=True)
            except asyncio.TimeoutError:
                # 如果超时未收到消息，继续下一次循环
                pass


if __name__ == "__main__":
    asyncio.run(main())
