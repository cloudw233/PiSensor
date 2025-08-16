import spidev
import time

from gpiozero import Button

class MCP3208_Joystick:
    def __init__(self):
        # 初始化SPI
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # 使用CE0 (GPIO8)
        self.spi.max_speed_hz = 1000000  # 1MHz SPI时钟
        self.button = Button(25)
        
    def read_channel(self, channel):
        """读取MCP3208指定通道的模拟值（0-7）"""
        # MCP3208的SPI通信协议：
        # 发送3字节：[开始位, 配置位, 空字节]
        # 接收3字节：[空字节, 高8位, 低8位]
        adc = self.spi.xfer2([
            0b00000110 | ((channel & 0b0100) >> 2),  # 开始位 + 单端模式 + 通道选择高位
            (channel & 0b0011) << 6,                 # 通道选择低位
            0x00                                     # 空字节
        ])
        # 组合高8位和低4位（MCP3208是12位ADC）
        value = ((adc[1] & 0x0F) << 8) | adc[2]
        return value
    
    def read_joystick(self):
        """读取摇杆X/Y轴的值（0-4095）"""
        x_val = self.read_channel(0)  # CH0接X轴
        y_val = self.read_channel(1)  # CH1接Y轴
        button_state = self.button.is_active
        return int(x_val/4), int(y_val/4), button_state
    
    def close(self):
        """关闭SPI连接和GPIO资源"""
        self.spi.close()
        self.button.close()

# 使用示例
if __name__ == "__main__":
    try:
        joystick = MCP3208_Joystick()
        while True:
            x, y, _ = joystick.read_joystick()
            print(f"X轴: {x:4d} | Y轴: {y:4d}", end="\r")
            time.sleep(0.1)
    except KeyboardInterrupt:
        joystick.close()
        print("\n程序终止")