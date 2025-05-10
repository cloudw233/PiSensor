import serial
import pynmea2

class ATK1218GPS:
    def __init__(self, port="/dev/ttyUSB1", baudrate=38400):
        # 初始化串口
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        
    def read_gps(self):
        """读取GPS数据"""
        try:
            while True:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                # print(f"接收到的数据: {line}")  # 添加调试信息
                
                # 只处理RMC和GGA语句
                if line.startswith('$GNRMC') or line.startswith('$GNGGA'):
                    try:
                        msg = pynmea2.parse(line)
                        if hasattr(msg, 'latitude') and hasattr(msg, 'longitude'):
                            # 格式化输出
                            print(f"纬度: {msg.latitude:.2f}°{msg.lat_dir}")
                            print(f"经度: {msg.longitude:.2f}°{msg.lon_dir}")
                            break
                            
                    except pynmea2.ParseError as e:
                        print(f"数据解析错误: {e}")
                        
        except KeyboardInterrupt:
            print("\n程序终止...")
            self.cleanup()
            
    def cleanup(self):
        """清理资源"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("串口已关闭")

if __name__ == "__main__":
    try:
        # 创建GPS对象
        gps = ATK1218GPS()
        gps.read_gps()
    except Exception as e:
        print(f"错误: {e}")