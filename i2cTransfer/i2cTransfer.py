import time
from smbus2 import SMBus, i2c_msg

# I2C设备地址定义
PCF8574_ADDR = 0x20   # PCF8574T地址(气体传感器和倾斜开关)
MAX30102_ADDR = 0x57  # MAX30102心率传感器地址
INA226_ADDR = 0x40    # INA226电压电流监测地址
PCF8591_ADDR = 0x48   # PCF8591 ADC地址

class IntegratedSensorHub:
    def __init__(self, bus_number=1):
        """初始化传感器集线器"""
        # 初始化I2C总线
        self.bus = SMBus(bus_number)
        
        # 传感器状态缓存
        self.last_tilt_state = False
        self.last_gas_readings = [False] * 6
        
        # 设备数据缓存
        self.device_data = {
            'pcf8574': 0,
            'ina226': {'voltage': 0.0},
            'pcf8591': [0, 0, 0, 0]
        }

        
    def read_tilt_switch(self):
        """
        读取倾斜开关状态 (PCF8574T P6)
        返回: (bool, bool) - (当前状态, 是否改变)
        """
        try:
            data = self.device_data['pcf8574']
            # 修改为直接读取P6引脚状态，低电平表示触发
            tilt_state = not bool(data & 0x40)  # 0x40 = 0b01000000，取P6引脚
            
            # 状态变化检测
            changed = tilt_state != self.last_tilt_state
            self.last_tilt_state = tilt_state
            
            return tilt_state, changed
        except Exception as e:
            return False, False
    
    def read_gas_sensors(self):
        """
        读取6个MQ气体传感器状态 (PCF8574T P0-P5)
        返回: (list, list) - (当前状态列表, 变化状态列表)
        """
        data = self.device_data['pcf8574']
        
        # 提取P0-P5的状态
        current_readings = [
            bool(data & (1 << i)) for i in range(0, 6)
        ]
        
        # 检测状态变化
        changes = [current != last for current, last in zip(current_readings, self.last_gas_readings)]
        self.last_gas_readings = current_readings
        
        return current_readings, changes

    def read_pcf8574(self):
        """读取PCF8574的8位输入状态"""
        try:
            msg = i2c_msg.read(PCF8574_ADDR, 1)
            self.bus.i2c_rdwr(msg)
            self.device_data['pcf8574'] = list(msg)[0]
            return True
        except Exception as e:
            print(f"PCF8574 READ ERROR: {e}")
            return False

    def read_ina226(self):
        """仅读取INA226的电压（优化版）"""
        try:
            # 读取电压寄存器（0x02）
            data = self.bus.read_i2c_block_data(INA226_ADDR, 0x02, 2)
            voltage_raw = (data[0] << 8) | data[1]
            
            # 计算原始电压值（1.25mV/LSB）
            voltage = voltage_raw * 0.00125  # 单位：V
            
            # 硬件校准补偿（实测12.5V但读数13.2V时的修正）
            compensation_factor = 12.5 / 13.2  # 校准系数
            calibrated_voltage = voltage * compensation_factor
            
            # 存储结果
            self.device_data['ina226']['voltage'] = round(calibrated_voltage, 2)
            return True
            
        except Exception as e:
            print(f"INA226 READ ERROR: {e}")
            return False

    def read_pcf8591(self):
        """读取PCF8591的前2个ADC通道并换算为电压"""
        try:
            self.bus.write_byte_data(PCF8591_ADDR, 0x04, 0x04)
            self.bus.read_byte(PCF8591_ADDR)  # 丢弃第一个字节
            adc_values = self.bus.read_i2c_block_data(PCF8591_ADDR, 0x00, 2)
                
                # 第一个通道参考电压5V，第二个通道参考电压为3.3V
            refer_vol = [5.0, 3.3]
            vol5v= [(adc_values[0] / 255.0) * refer_vol[0] ]
            vol3v3= [(adc_values[1] / 255.0) * refer_vol[1] ]   
            self.device_data['pcf8591'] = vol5v,vol3v3
            return True
        except Exception as e:
            print(f"PCF8591 READ ERROR: {e}")
            return False

    def read_all(self):
        """读取所有传感器数据"""
        # 读取PCF8574数据(倾斜和气体传感器)
        self.read_pcf8574()
        
        # 获取倾斜和气体传感器数据
        tilt_state, tilt_changed = self.read_tilt_switch()
        gas_readings, gas_changes = self.read_gas_sensors()
        
        # 读取其他传感器
        self.read_ina226()
        self.read_pcf8591()
        
        # 返回完整的数据集
        return {
            "tilt": {
                "state": tilt_state,
                "changed": tilt_changed
            },
            "gas_sensors": {
                "MQ2": gas_readings[0],
                "MQ7": gas_readings[3],  # 保持原有索引
                "changes": gas_changes
            },
            "power": self.device_data['ina226'],
            "adc": {
                "5v": self.device_data['pcf8591'][0],
                "3.3v": self.device_data['pcf8591'][1]

            },
            "timestamp": time.time()
        }

    def close(self):
        """清理资源"""
        self.bus.close()

def main():
    """主程序"""
    sensor_hub = IntegratedSensorHub()
    
    try:
        while True:
            sensor_data = sensor_hub.read_all()
            print("\nSensorDATA：")
            
            # 倾斜检测
            print(f"[Tilt] {'true' if sensor_data['tilt']['state'] else 'false'}")
                
            # 气体传感器
            gas_sensors = {
                'MQ2': 'smoke',
                'MQ7': 'CO'
            }
            
            for gas, desc in gas_sensors.items():
                state = "true" if sensor_data["gas_sensors"][gas] else "false"
                print(f"[{gas}] {desc}: {state}")
            
            # 电源监控
            print(f"[12v] {sensor_data['power']['voltage']:.2f}v")
                  
            # ADC数据
            adc_data = sensor_data['adc']
            print(f"[5v] {adc_data['5v'][0]:.1f}v")    
            print(f"[3.3v] {adc_data['3.3v'][0]:.1f}v") 

            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n程序终止")
    finally:
        sensor_hub.close()

if __name__ == "__main__":
    main()