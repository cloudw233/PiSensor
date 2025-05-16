import serial
import pynmea2

class Locator:
    def __init__(self, port="/dev/ttyUSB0", baudrate=38400):
        # 初始化串口
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        
    def read_location(self):
        try:
            while True:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('$GNRMC') or line.startswith('$GNGGA'):
                    try:
                        msg = pynmea2.parse(line)
                        if all((hasattr(msg, 'latitude'),hasattr(msg, 'longitude'),int(msg.latitude)!=0,int(msg.longitude)!=0)):
                            # 格式化输出
                            return f"{msg.latitude:.2f}°{msg.lat_dir}", f"{msg.longitude:.2f}°{msg.lon_dir}"
                            
                    except pynmea2.ParseError as e:
                        print(f"数据解析错误: {e}")
                        
        except KeyboardInterrupt:
            print("\n程序终止...")
            self.cleanup()
            return None

    def cleanup(self):
        """清理资源"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("串口已关闭")

if __name__ == "__main__":
    try:
        gnss = Locator()
        print(gnss.read_location())
    except Exception as e:
        print(f"错误: {e}")