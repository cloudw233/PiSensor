import time
from smbus2 import SMBus, i2c_msg

# I2C设备地址定义
PCF8574_ADDR = 0x20   # PCF8574T地址(气体传感器和倾斜开关)
MAX30102_ADDR = 0x57  # MAX30102心率传感器地址
INA226_ADDR = 0x40    # INA226电压电流监测地址
PCF8591_ADDR = 0x48   # PCF8591 ADC地址
REG_INTR_STATUS_1 = 0x00
REG_INTR_STATUS_2 = 0x01
REG_INTR_ENABLE_1 = 0x02
REG_INTR_ENABLE_2 = 0x03
REG_FIFO_WR_PTR = 0x04
REG_FIFO_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_FIFO_DATA = 0x07
REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A
REG_LED1_PA = 0x0C  # LED1 亮度（红光）
REG_LED2_PA = 0x0D  # LED2 亮度（红外光）
REG_PILOT_PA = 0x10
REG_MULTI_LED_CTRL1 = 0x11
REG_MULTI_LED_CTRL2 = 0x12
REG_TEMP_INTR = 0x1F
REG_TEMP_FRAC = 0x20
REG_TEMP_CONFIG = 0x21
REG_PROX_INT_THRESH = 0x30
REG_REV_ID = 0xFE
REG_PART_ID = 0xFF

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
            'max30102': {'red': 0, 'ir': 0},
            'ina226': {'voltage': 0.0},
            'pcf8591': [0, 0, 0, 0]
        }
        self.device_data = {
            'pcf8574': 0,
            'max30102': {
                'heart_rate': 0,
                'finger_detected': False,
                'signal_quality': 0
            },
            'ina226': {'voltage': 0.0},
            'pcf8591': [0, 0, 0, 0]
        }

        # 心率计算相关变量
        self.ir_samples = []
        self.last_beat_time = time.time()
        self.beats_count = 0
        self.sampling_start_time = time.time()

    def calculate_heart_rate(self, ir_value):
        """计算心率"""
        SAMPLE_RATE = 100      # 采样率 Hz
        MIN_HR = 45           # 最小心率 BPM
        MAX_HR = 200          # 最大心率 BPM
        FINGER_THRESHOLD = 30000  # 手指检测阈值
        PEAK_THRESHOLD = 1.005   # 降低峰值检测阈值
        MIN_PEAK_INTERVAL = 0.3  # 最小峰值间隔（秒）
        
        current_time = time.time()
        
        # 检查是否有手指放置
        if ir_value < FINGER_THRESHOLD:
            self.device_data['max30102']['finger_detected'] = False
            self.device_data['max30102']['heart_rate'] = 0
            self.ir_samples = []
            self.last_beat_time = current_time
            return
        
        self.device_data['max30102']['finger_detected'] = True
        self.ir_samples.append((current_time, ir_value))
        
        # 保持3秒的采样窗口
        while self.ir_samples and (current_time - self.ir_samples[0][0]) > 3.0:
            self.ir_samples.pop(0)
        
        # 至少需要0.5秒的数据
        if len(self.ir_samples) >= 50:
            # 使用移动平均平滑数据
            window_size = 4
            smoothed_samples = []
            for i in range(len(self.ir_samples) - window_size + 1):
                avg_value = sum(x[1] for x in self.ir_samples[i:i+window_size]) / window_size
                smoothed_samples.append((self.ir_samples[i+window_size-1][0], avg_value))
            
            # 峰值检测
            peaks = []
            for i in range(1, len(smoothed_samples)-1):
                _, prev_val = smoothed_samples[i-1]
                curr_time, curr_val = smoothed_samples[i]
                _, next_val = smoothed_samples[i+1]
                
                if (curr_val > prev_val and 
                    curr_val > next_val and 
                    curr_val > prev_val * PEAK_THRESHOLD):
                    
                    # 检查是否与上一个峰值间隔足够
                    if not peaks or (curr_time - peaks[-1][0]) >= MIN_PEAK_INTERVAL:
                        peaks.append((curr_time, curr_val))
            
            # 计算心率
            if len(peaks) >= 2:
                # 使用多个峰值间隔的平均值
                intervals = []
                for i in range(1, len(peaks)):
                    interval = peaks[i][0] - peaks[i-1][0]
                    if interval > 0:
                        bpm = 60 / interval
                        if MIN_HR <= bpm <= MAX_HR:
                            intervals.append(bpm)
                
                if intervals:
                    avg_bpm = sum(intervals) / len(intervals)
                    
                    # 平滑心率输出
                    if self.device_data['max30102']['heart_rate'] == 0:
                        self.device_data['max30102']['heart_rate'] = int(avg_bpm)
                    else:
                        current_hr = self.device_data['max30102']['heart_rate']
                        new_hr = int((current_hr * 0.7) + (avg_bpm * 0.3))
                        self.device_data['max30102']['heart_rate'] = new_hr
                    print(f"检测到心跳峰值数: {len(peaks)}, 计算心率: {new_hr} BPM")

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
            print(f"倾斜开关读取错误: {e}")
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
            print(f"PCF8574读取错误: {e}")
            return False
            
    def read_max30102(self):
        """读取和初始化MAX30102心率传感器"""
        try:
            # 1. 检查传感器是否存在并打印调试信息
            part_id = self.bus.read_byte_data(MAX30102_ADDR, REG_PART_ID)
            rev_id = self.bus.read_byte_data(MAX30102_ADDR, REG_REV_ID)
            print(f"MAX30102 ID: 0x{part_id:02X}, REV: 0x{rev_id:02X}")
            
            if part_id != 0x15:
                print(f"MAX30102器件ID错误: 0x{part_id:02X}")
                return False

            # 2. 软复位并等待
            self.bus.write_byte_data(MAX30102_ADDR, REG_MODE_CONFIG, 0x40)
            time.sleep(0.1)

            # 3. 完整配置序列
            # 禁用所有中断
            self.bus.write_byte_data(MAX30102_ADDR, REG_INTR_ENABLE_1, 0x00)
            self.bus.write_byte_data(MAX30102_ADDR, REG_INTR_ENABLE_2, 0x00)
            
            # 配置FIFO
            self.bus.write_byte_data(MAX30102_ADDR, REG_FIFO_WR_PTR, 0x00)
            self.bus.write_byte_data(MAX30102_ADDR, REG_FIFO_RD_PTR, 0x00)
            self.bus.write_byte_data(MAX30102_ADDR, REG_FIFO_OVF_COUNTER, 0x00)
            
            # 配置模式
            self.bus.write_byte_data(MAX30102_ADDR, REG_MODE_CONFIG, 0x03)  # SpO2模式
            
            # 配置SPO2（采样率=100Hz，ADC量程=16384）
            self.bus.write_byte_data(MAX30102_ADDR, REG_SPO2_CONFIG, 0x47)  # 0x47: 100Hz, 16384, 411us
            
            # 增加LED亮度
            self.bus.write_byte_data(MAX30102_ADDR, REG_LED1_PA, 0x7F)  # 红光LED ~24mA
            self.bus.write_byte_data(MAX30102_ADDR, REG_LED2_PA, 0x7F)  # 红外LED ~24mA

            # 4. 等待数据
            time.sleep(0.1)  # 等待至少一个样本
            
            # 5. 读取FIFO数据
            num_samples = self.bus.read_byte_data(MAX30102_ADDR, REG_FIFO_WR_PTR) - \
                        self.bus.read_byte_data(MAX30102_ADDR, REG_FIFO_RD_PTR)
            
            
            if num_samples > 0:
                ir_sum = 0
                samples_read = 0
                for _ in range(min(num_samples, 4)):
                    data = self.bus.read_i2c_block_data(MAX30102_ADDR, REG_FIFO_DATA, 6)
                    ir = ((data[3] << 16) | (data[4] << 8) | data[5]) & 0x3FFFF
                    ir_sum += ir
                    samples_read += 1
                    self.calculate_heart_rate(ir)
                
            print(f"平均IR值: {ir_sum/samples_read:.0f}")  # 调试信息
            return True
            
        except Exception as e:
            print(f"MAX30102读取错误: {e}")
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
            print(f"INA226电压读取错误: {e}")
            return False

    def read_pcf8591(self):
        """读取PCF8591的前2个ADC通道并换算为电压"""
        try:
            self.bus.write_byte_data(PCF8591_ADDR, 0x04, 0x04)
            self.bus.read_byte(PCF8591_ADDR)  # 丢弃第一个字节
            adc_values = self.bus.read_i2c_block_data(PCF8591_ADDR, 0x00, 2)
                
                # 第一个通道参考电压为5V，第二个通道参考电压为3.3V
            reference_voltages = [5.0, 3.3]
            voltages = [(adc_values[i] / 255.0) * reference_voltages[i] for i in range(2) ]
                
            self.device_data['pcf8591'] = voltages
            return True
        except Exception as e:
            print(f"PCF8591读取错误: {e}")
            return False

    def read_all_sensors(self):
        """读取所有传感器数据"""
        # 读取PCF8574数据(倾斜和气体传感器)
        self.read_pcf8574()
        
        # 获取倾斜和气体传感器数据
        tilt_state, tilt_changed = self.read_tilt_switch()
        gas_readings, gas_changes = self.read_gas_sensors()
        
        # 读取其他传感器
        self.read_max30102()
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
                "MQ4": gas_readings[1],
                "MQ5": gas_readings[2],
                "MQ7": gas_readings[3],
                "MQ9": gas_readings[4],
                "MQ135": gas_readings[5],
                "changes": gas_changes
            },
            "heart_rate": self.device_data['max30102'],
            "power": self.device_data['ina226'],
            "adc": self.device_data['pcf8591'],
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
            sensor_data = sensor_hub.read_all_sensors()
            
            print(f"传感器数据：")

          # 倾斜状态（添加更多调试信息）
            tilt_status = "倾斜" if sensor_data["tilt"]["state"] else "水平"
            print(f"[倾斜开关] 当前状态: {tilt_status}")
            
            
            # 气体传感器状态
            gas_status = []
            for gas, reading in zip(
                ["MQ2", "MQ4", "MQ5", "MQ7", "MQ9", "MQ135"],
                sensor_data["gas_sensors"]["changes"]
            ):
                if reading:
                    state = "检测到气体" if sensor_data["gas_sensors"][gas] else "气体消失"
                    gas_status.append(f"{gas}: {state}")
            
            if gas_status:
                print("[气体传感器] " + ", ".join(gas_status))
           
            # 心率传感器数据
            if sensor_data['heart_rate']['finger_detected']:
                if sensor_data['heart_rate']['heart_rate'] > 0:
                    print(f"[心率传感器] 心率: {sensor_data['heart_rate']['heart_rate']} BPM")
                else:
                    print("[心率传感器] 正在计算心率...")
            else:
                print("[心率传感器] 未检测到手指")
            
            
            # 电源监测
            print(f"[12v电源状态] 电压: {sensor_data['power']['voltage']:.3f}V")
            
            # ADC数据
            print(f"[5v与3.3v] 电压: {sensor_data['adc']}")
            
            time.sleep(1)  # 1秒采样间隔
            
    except KeyboardInterrupt:
        print("\n程序终止")
    finally:
        sensor_hub.close()

if __name__ == "__main__":
    main()