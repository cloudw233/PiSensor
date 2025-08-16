import logging
import uvicorn
import threading
import time

from fastapi import FastAPI
from loguru import logger

from core.builtins.elements import StepperMotorElements, HeartElements, MachineryElements
from core.builtins.message_constructors import MessageChain, MessageChainD
from core.builtins.assigned_element import SensorElement, AccountElement
from core.message_queue import message_queue_manager
from core.constants import QueueNames

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

def relay_server_thread():
    """
    中继服务器线程函数，处理消息转发
    """
    # 创建与各模块通信的队列
    heart_queue = message_queue_manager.get_queue(QueueNames.HEART)
    step_motor_queue = message_queue_manager.get_queue(QueueNames.STEP_MOTOR)
    wheel_queue = message_queue_manager.get_queue(QueueNames.WHEEL)
    
    while True:
        try:
            # 从主队列接收消息
            data = message_queue_manager.receive_message(QueueNames.MAIN, timeout=1)
            if data is not None:
                logger.debug(data)
                # 发送传感器数据
                message_queue_manager.send_message(QueueNames.MAIN_RESPONSE, MessageChain([account, sensor]))
                sensor.urgent_button = False
                parsed_msg = MessageChainD(data)
                parsed_msg.serialize()
                step_e = [_ for _ in parsed_msg.messages if isinstance(_, StepperMotorElements)]
                heart_e = [_ for _ in parsed_msg.messages if isinstance(_, HeartElements)]
                wheel_e = [_ for _ in parsed_msg.messages if isinstance(_, MachineryElements)]
                for e in [step_e, heart_e, wheel_e]:
                    if len(e) > 0:
                        if e == step_e:
                            step_motor_queue.put(MessageChain([account, e[0]]).deserialize())
                        elif e == heart_e:
                            heart_queue.put(MessageChain([account, e[0]]).deserialize())
                        elif e == wheel_e:
                            wheel_queue.put(MessageChain([account, e[0]]).deserialize())
        except Exception as e:
            logger.error(f"Error in relay server: {e}")
            time.sleep(1)


@app.post("/api/sensor/{path}")
def sensor_data_handler(path: str, data: dict):
    """
    处理传感器数据
    """
    try:
        match path:
            case 'humiture':
                sensor.temp = data['temperature']
                sensor.humidity = data['humidity']
            case 'smbus':
                sensor.tilt = data['tilt']
                sensor.smoke["MQ_2"] = data['gas_sensors']['MQ2']
                sensor.smoke["MQ_7"] = data['gas_sensors']['MQ7']
                sensor.power = data['power']
            case 'urgent_button':
                sensor.urgent_button = data['value']
            case 'location':
                sensor.gps = data['value']
            case 'heart':
                sensor.heart_data = data['value']
    except Exception as e:
        logger.error(f"Error handling sensor data for {path}: {e}")


def run_relay_server():
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

        # 启动中继服务器线程
        relay_thread = threading.Thread(target=relay_server_thread, daemon=True)
        relay_thread.start()
        
        config = uvicorn.Config(app, host="localhost", port=int(10240), access_log=True, workers=2)
        server = uvicorn.Server(config)
        init_logger()
        server.run()
    except Exception as e:
        logger.error(f"Error in relay server: {e}")