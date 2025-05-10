import serial
import time
import sys
from typing import List, Optional

class RD03ERadar:
    def __init__(self, port='/dev/ttyUSB0', baudrate=256000):
        """初始化雷达"""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1  # 添加超时
            )
            self.buffer = bytearray()
            print(f"雷达初始化成功: {port}")
        except Exception as e:
            print(f"雷达初始化失败: {e}", file=sys.stderr)
            raise

    def read_distance(self) -> Optional[float]:
        try:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting)
                print(data)
                data = [r"\x"+i for i in ("aaaa"+data.hex("::").split('aaaa')[0]).split("::")]
                data = bytes(data.join())
                self.buffer.extend(data)
                # 查找帧头和完整帧
                while len(self.buffer) >= 7:
                    if self.buffer[0:2] == b'\xaa\xaa':
                        frame = bytes(self.buffer[:7])
                        self.buffer = self.buffer[7:]
                        
                        result = self.parse_frame(frame)
                        if result:
                            return result['distance']
                    else:
                        self.buffer.pop(0)
            return None
            
        except Exception as e:
            print(f"读取错误: {e}", file=sys.stderr)
            return None

    def parse_frame(self, frame: bytes) -> Optional[dict]:
        """解析数据帧: AA AA 02 XX XX 55 55"""
        try:
            if len(frame) < 7:  # 检查帧长度
                return None
                
            # 检查帧头和帧尾
            if (frame[0:2] != b'\xaa\xaa' or
                frame[-2:] != b'\x55\x55'):
                return None
                
            # 合并两个字节为距离值
            distance = (frame[3] << 8) | frame[4]  # 高字节在前
            
            print(f"原始字节: {frame[3]:02x} {frame[4]:02x}, 距离: {distance}cm")
            
            return {
                'distance': distance,
                'raw': frame.hex()
            }
            
        except Exception as e:
            print(f"解析错误: {e}", file=sys.stderr)
            return None

    def close(self):
        """关闭串口"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()

def main():
    radar = None
    try:
        radar = RD03ERadar()
        print("开始读取数据...")
        
        while True:
            if radar.ser.in_waiting:  # 检查是否有数据
                raw_data = radar.ser.read(radar.ser.in_waiting)
                print(f"原始数据: {raw_data.hex()}")  # 打印原始数据
                
                distance = radar.read_distance()
                if distance:
                    print(f"检测距离: {distance:.1f}cm")
                else:
                    print("解析距离失败")
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n程序终止")
    except Exception as e:
        print(f"运行错误: {e}", file=sys.stderr)
    finally:
        if radar:
            radar.close()

if __name__ == "__main__":
    main()