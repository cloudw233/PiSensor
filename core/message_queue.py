import queue
import threading
from typing import Dict, Any
from loguru import logger

class MessageQueueManager:
    """
    管理模块间通信的队列系统
    """
    def __init__(self):
        self.queues: Dict[str, queue.Queue] = {}
        self.lock = threading.Lock()
    
    def get_queue(self, name: str) -> queue.Queue:
        """
        获取指定名称的队列，如果不存在则创建
        """
        with self.lock:
            if name not in self.queues:
                self.queues[name] = queue.Queue()
                logger.info(f"Created queue: {name}")
            return self.queues[name]
    
    def send_message(self, queue_name: str, message: Any) -> bool:
        """
        向指定队列发送消息
        """
        try:
            q = self.get_queue(queue_name)
            q.put(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {queue_name}: {e}")
            return False
    
    def receive_message(self, queue_name: str, timeout: float = None) -> Any:
        """
        从指定队列接收消息
        """
        try:
            q = self.get_queue(queue_name)
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Failed to receive message from {queue_name}: {e}")
            return None

# 全局消息队列管理器实例
message_queue_manager = MessageQueueManager()