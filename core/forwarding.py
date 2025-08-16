import threading
import time
import websocket

from config import config
from loguru import logger
from core.message_queue import message_queue_manager

def forward_messages():
    while True:
        try:
            # 连接到远程服务器
            remote = websocket.create_connection(config('remote-server'))
            logger.info("Successfully connected to remote server.")
            
            # 获取消息队列
            main_queue = message_queue_manager.get_queue('main')
            main_response_queue = message_queue_manager.get_queue('main_response')
            
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
                
                # 转发消息
                if recv_relay is not None:
                    remote.send(recv_relay)
                
                # 短暂休眠以避免过度占用CPU
                time.sleep(0.01)
        except (websocket.WebSocketConnectionClosedException, ConnectionRefusedError, ConnectionResetError) as e:
            logger.error(f"Connection to remote server lost: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"An unexpected error occurred in message forwarding: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        finally:
            # 确保连接被正确关闭
            if 'remote' in locals() and remote.connected:
                remote.close()
