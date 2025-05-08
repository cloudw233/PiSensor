#!/usr/bin/env python3
import serial
import threading
import time
from dataclasses import dataclass

@dataclass
class RadarData:
    x: float
    y: float
    speed: float
    distance_resolution: float

class LD2450Reader:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.running = True
        self.data = RadarData(0, 0, 0, 0)
        self.lock = threading.Lock()
        
    def start(self):
        self.thread = threading.Thread(target=self._read_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        self.thread.join()
        self.ser.close()
        
    def _read_loop(self):
        """持续读取雷达数据并解析"""
        buffer = bytearray()
        while self.running:
            # 读取数据
            data = self.ser.read(self.ser.in_waiting or 1)
            if not data:
                continue
                
            buffer.extend(data)
            
            # 查找帧头 (假设协议以0xAA 0x55开头)
            while len(buffer) >= 2:
                if buffer[0] == 0xAA and buffer[1] == 0x55:
                    # 检查是否收到完整帧 (假设帧长20字节)
                    if len(buffer) >= 20:
                        frame = buffer[:20]
                        buffer = buffer[20:]
                        self._parse_frame(frame)
                    else:
                        break
                else:
                    buffer.pop(0)
    
    def _parse_frame(self, frame):
        """解析LD2451数据帧"""
        # 示例解析 - 根据实际协议修改
        # 假设数据格式: 0xAA 0x55 [x(2byte)] [y(2byte)] [speed(2byte)] [res(2byte)] [CRC]
        try:
            x = int.from_bytes(frame[2:4], byteorder='little', signed=True) / 100.0
            y = int.from_bytes(frame[4:6], byteorder='little', signed=True) / 100.0
            speed = int.from_bytes(frame[6:8], byteorder='little', signed=True) / 100.0
            res = int.from_bytes(frame[8:10], byteorder='little') / 100.0
            
            with self.lock:
                self.data = RadarData(x, y, speed, res)
        except Exception as e:
            print(f"解析错误: {e}")

def find_ch340_devices():
    """查找所有CH340设备"""
    import glob
    return glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')

def main():
    # 初始化所有雷达读取器
    radars = []
    ports = find_ch340_devices()
    
    if not ports:
        print("未检测到CH340设备!")
        return
    
    print(f"检测到{len(ports)}个串口设备: {ports}")
    
    for i, port in enumerate(ports[:4]):  # 最多处理4个雷达
        try:
            reader = LD2450Reader(port)
            reader.start()
            radars.append(reader)
            print(f"雷达{i+1} 已连接: {port}")
        except Exception as e:
            print(f"无法打开端口 {port}: {e}")
    
    if not radars:
        print("没有可用的雷达设备!")
        return
    
    try:
        # 主循环: 打印所有雷达数据
        while True:
            print("\n" + "="*40)
            for i, radar in enumerate(radars):
                with radar.lock:
                    data = radar.data
                print(f"雷达{i+1}: X={data.x:.2f}m, Y={data.y:.2f}m, "
                      f"速度={data.speed:.2f}m/s, 分辨率={data.distance_resolution:.3f}m")
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n正在停止...")
        for radar in radars:
            radar.stop()

if __name__ == "__main__":
    main()