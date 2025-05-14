import websockets
import asyncio

from gpiozero import Button

urgent_button = Button(16)

async def run():
    try:
        while True:
            urgent_button.wait_for_active()
            async with websockets.connect("ws://localhost:10240/urgent-button") as ws:
                await ws.send("urgent")
    except asyncio.CancelledError:
        raise

