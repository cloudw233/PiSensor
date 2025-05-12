import board
import adafruit_dht
from loguru import logger


# 初始化DHT11，数据线接在GPIO4
def get_humiture():
    dht_device = adafruit_dht.DHT11(board.D1)

    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity
        dht_device.exit()
        if humidity and temperature:
            return temperature, humidity
        return None
    except Exception as e:
        logger.error(f"[Humiture]读取出错: {e}")
        dht_device.exit()
        return None
