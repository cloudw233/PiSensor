import serial
import time

def send_and_receive():
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        
        # 发送命令
        command = b'\xFD\xFC\xFB\xFA\x02\x00\xA3\x00\x04\x03\x02\x01'  # 示例命令
        print(f"发送: {command.hex(' ').upper()}")
        ser.write(command)
        
        # 等待并读取响应
        time.sleep(0.1)  # 根据模块响应时间调整
        response = ser.read_all()
        print(f"收到响应: {response.hex(' ').upper()}")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'ser' in locals():
            ser.close()

send_and_receive()