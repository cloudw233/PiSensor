import board
import adafruit_dht
from loguru import logger


# 初始化DHT11，数据线接在GPIO4
def get_humiture():
    dht_device = None
    try:
        dht_device = adafruit_dht.DHT11(board.D1)
        temperature = dht_device.temperature
        humidity = dht_device.humidity
        
        if humidity is not None and temperature is not None:
            return temperature, humidity
        else:
            logger.warning("[Humiture] Received None values from sensor")
            return 25.0, 50.0  # 返回默认值
            
    except RuntimeError as e:
        if "Timed out waiting for PulseIn message" in str(e):
            logger.warning(f"[Humiture] Sensor timeout, using default values: {e}")
            return 25.0, 50.0  # 返回默认值而不是None
        else:
            logger.error(f"[Humiture] Runtime error: {e}")
            return 25.0, 50.0
    except Exception as e:
        logger.error(f"[Humiture] Unexpected error: {e}")
        return 25.0, 50.0
    finally:
        if dht_device:
            try:
                dht_device.exit()
            except:
                pass

if __name__ == "__main__":
    print(get_humiture())
