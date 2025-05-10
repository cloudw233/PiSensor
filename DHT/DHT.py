import time
import board
import adafruit_dht

# 初始化DHT11，数据线接在GPIO4
dht_device = adafruit_dht.DHT11(board.D1)

try:
    temperature = dht_device.temperature
    humidity = dht_device.humidity
    if humidity is not None and temperature is not None:
        print(f"温度: {temperature}°C  湿度: {humidity}%")
    else:
        print("读取失败，请检查传感器连接")
except Exception as e:
    print(f"读取出错: {e}")
finally:
    dht_device.exit()