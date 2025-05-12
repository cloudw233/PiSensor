import importlib

from fastapi import FastAPI, WebSocket
from multiprocessing import Process

from contextlib import asynccontextmanager

def go(module:str):
    importlib.import_module(f"driver.{module}.run")
    

@asynccontextmanager
async def lifespan(app:FastAPI):

    yield

app = FastAPI()