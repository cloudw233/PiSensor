import serial
import threading
import time
import sys
import glob

class RadarData:
    def __init__(self, distance=0, speed=0, signal_strength=0):
        self.distance = distance        # 距离(米)
        self.speed = speed             # 速度(米/秒)
        self.signal_strength = signal_strength  # 信号强度

class RadarReader:
    def __init__(self, port, baudrate=256000):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.data = RadarData()
        self.lock = threading.Lock()
        self.running = True
        
    def parse_frame(self, frame):
        """解析RD-03E雷达数据帧"""
        try:
            # 检查帧头
            if frame[0] != 0xAA or frame[1] != 0x55:
                raise ValueError("无效的帧头")
                
            # 检查帧长度
            if len(frame) < 8:
                raise ValueError("数据帧长度不足")
                
            # 检查校验和
            checksum = sum(frame[:-1]) & 0xFF
            if checksum != frame[-1]:
                raise ValueError(f"校验和错误: 计算值{checksum}, 接收值{frame[-1]}")
            
            # 解析数据
            distance = ((frame[3] << 8) | frame[2]) / 100.0  # 距离(米)
            speed = ((frame[5] << 8) | frame[4]) / 100.0     # 速度(米/秒)
            signal_strength = frame[6]  # 信号强度
            
            with self.lock:
                self.data = RadarData(distance, speed, signal_strength)
                
        except Exception as e:
            print(f"解析错误: {e}")
            
    def read_loop(self):
        """读取雷达数据的循环"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            
            buffer = bytearray()
            while self.running:
                if self.ser.in_waiting:
                    data = self.ser.read()
                    buffer.extend(data)
                    
                    # 查找帧头
                    while len(buffer) >= 2 and (buffer[0] != 0xAA or buffer[1] != 0x55):
                        buffer.pop(0)
                        
                    # 完整帧长度为8字节
                    if len(buffer) >= 8:
                        self.parse_frame(buffer[:8])
                        buffer = buffer[8:]
                        
        except Exception as e:
            print(f"读取错误: {e}")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

    def start(self):
        """启动雷达读取线程"""
        self.running = True
        self.thread = threading.Thread(target=self.read_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """停止雷达读取"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1)
        if self.ser and self.ser.is_open:
            self.ser.close()

def find_radar_devices():
    """查找所有串口设备"""
    return glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')

def main():
    # 查找可用的串口设备
    ports = find_radar_devices()
    if not ports:
        print("未检测到雷达设备!")
        return
        
    print(f"检测到{len(ports)}个串口设备: {ports}")
    
    # 初始化雷达读取器
    radars = []
    try:
        for port in ports[:4]:  # 最多支持4个雷达
            radar = RadarReader(port)
            radar.start()
            radars.append(radar)
            
        # 主循环
        while True:
            for i, radar in enumerate(radars):
                with radar.lock:
                    data = radar.data
                print(f"雷达 {i+1}: 距离={data.distance:.2f}m, 速度={data.speed:.2f}m/s, 信号强度={data.signal_strength}")
            time.sleep(0.1)  # 100ms更新间隔
            
    except KeyboardInterrupt:
        print("\n程序终止")
    finally:
        for radar in radars:
            radar.stop()

if __name__ == "__main__":
    main()