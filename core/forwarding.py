import asyncio
import websockets

from config import config
from loguru import logger


async def forward_messages():
    try:
        async with websockets.connect(config('remote-server')) as remote, websockets.connect("ws://localhost:10240/server") as relay:
            while True:
                recv_remote, recv_relay = await asyncio.gather(
                    remote.recv(),
                    relay.recv()
                )
                logger.debug(f"Received from remote: {recv_remote}")
                await asyncio.gather(
                    remote.send(recv_relay),
                    relay.send(recv_remote)
                )
    except asyncio.CancelledError:
        raise
