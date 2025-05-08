#!/usr/bin/env python3
import serial
import threading
import time
import sys

class SerialRawReader:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.running = True
        
    def start(self):
        self.thread = threading.Thread(target=self._read_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        self.thread.join()
        self.ser.close()
        
    def _read_loop(self):
        """持续读取并输出原始串口数据"""
        while self.running:
            data = self.ser.read(self.ser.in_waiting or 1)
            if data:
                # 以16进制和ASCII形式显示原始数据
                hex_str = ' '.join(f'{b:02X}' for b in data)
                ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
                print(f"[{self.ser.port}] HEX: {hex_str} | ASCII: {ascii_str}")

def find_ch340_devices():
    """查找所有CH340设备"""
    import glob
    return glob.glob('/dev/ttyUSB*')

def main():
    # 初始化所有串口读取器
    readers = []
    ports = find_ch340_devices()
    
    if not ports:
        print("未检测到CH340设备!", file=sys.stderr)
        return
    
    print(f"检测到{len(ports)}个串口设备: {ports}")
    
    for port in ports[:4]:  # 最多处理4个设备
        try:
            reader = SerialRawReader(port)
            reader.start()
            readers.append(reader)
            print(f"已开始监听: {port}")
        except Exception as e:
            print(f"无法打开端口 {port}: {e}", file=sys.stderr)
    
    if not readers:
        print("没有可用的串口设备!", file=sys.stderr)
        return
    
    try:
        # 主循环保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止监听...")
        for reader in readers:
            reader.stop()

if __name__ == "__main__":
    main()