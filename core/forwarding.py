import threading
import time
import websocket

from config import config
from loguru import logger
from core.message_queue import message_queue_manager
from core.builtins.elements import StepperMotorElements, HeartElements, MachineryElements
from core.builtins.message_constructors import MessageChain, MessageChainD
from core.builtins.assigned_element import SensorElement, AccountElement
from core.constants import QueueNames

sensor_lock = threading.Lock()

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

def message_processing_thread():
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


def sensor_data_aggregator():
    """
    Aggregates sensor data from various queues.
    """
    queues = {
        QueueNames.HUMITURE: message_queue_manager.get_queue(QueueNames.HUMITURE),
        QueueNames.SMBUS: message_queue_manager.get_queue(QueueNames.SMBUS),
        QueueNames.LOCATOR: message_queue_manager.get_queue(QueueNames.LOCATOR),
        QueueNames.HEART: message_queue_manager.get_queue(QueueNames.HEART),
    }

    while True:
        for queue_name, queue in queues.items():
            try:
                data = queue.get(timeout=0.01)
                with sensor_lock:
                    if queue_name == QueueNames.HUMITURE:
                        sensor.temp = data['temperature']
                        sensor.humidity = data['humidity']
                    elif queue_name == QueueNames.SMBUS:
                        sensor.tilt = data['tilt']
                        sensor.smoke["MQ_2"] = data['gas_sensors']['MQ2']
                        sensor.smoke["MQ_7"] = data['gas_sensors']['MQ7']
                        sensor.power = data['power']
                    elif queue_name == QueueNames.LOCATOR:
                        sensor.gps = data
                    elif queue_name == QueueNames.HEART:
                        sensor.heart_data = data
                message_queue_manager.send_message(QueueNames.SENSOR_DATA, MessageChain([account, sensor]))
            except Exception as e:
                pass
        time.sleep(0.1)


def forward_messages():
    retry_delay = 1
    while True:
        try:
            # 连接到远程服务器
            remote = websocket.create_connection(config('remote-server'))
            logger.info("Successfully connected to remote server.")
            
            # 获取消息队列
            main_queue = message_queue_manager.get_queue('main')
            main_response_queue = message_queue_manager.get_queue('main_response')
            sensor_data_queue = message_queue_manager.get_queue('sensor_data')
            
            while True:
                # 从远程服务器接收消息
                recv_remote = remote.recv()
                logger.debug(f"Received from remote: {recv_remote}")
                
                # 将远程消息发送到主队列
                message_queue_manager.send_message('main', recv_remote)
                
                # 从主响应队列接收消息
                recv_relay = None
                try:
                    recv_relay = main_response_queue.get(timeout=0.01)
                except:
                    pass
                
                # 从传感器数据队列接收消息
                try:
                    sensor_data = sensor_data_queue.get(timeout=0.01)
                    if sensor_data is not None:
                        remote.send_text(sensor_data)

                except:
                    pass
                
                # 转发消息
                if recv_relay is not None:
                    remote.send_text(recv_relay)
                
                # 短暂休眠以避免过度占用CPU
                time.sleep(0.01)
        except (websocket.WebSocketConnectionClosedException, ConnectionRefusedError, ConnectionResetError) as e:
            logger.error(f"Connection to remote server lost: {e}. Reconnecting in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)  # Exponential backoff, max 60s
        except Exception as e:
            logger.error(f"An unexpected error occurred in message forwarding: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
        finally:
            if 'remote' in locals() and remote.connected:
                remote.close()

def run_servers():
    try:
        # Start message processing thread
        processing_thread = threading.Thread(target=message_processing_thread, daemon=True)
        processing_thread.start()

        # Start sensor data aggregator thread
        aggregator_thread = threading.Thread(target=sensor_data_aggregator, daemon=True)
        aggregator_thread.start()

        # Start message forwarding thread
        forwarding_thread = threading.Thread(target=forward_messages, daemon=True)
        forwarding_thread.start()

        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in forwarding/relay server: {e}")

