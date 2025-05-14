import smbus2
import time
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

# MAX30102 I2C地址和寄存器定义
MAX30102_ADDR = 0x57
REG_FIFO_DATA = 0x07
REG_INTR_ENABLE_1 = 0x02
REG_INTR_ENABLE_2 = 0x03
REG_FIFO_WR_PTR = 0x04
REG_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A
REG_LED1_PA = 0x0C
REG_LED2_PA = 0x0D

bus = smbus2.SMBus(1)

def write_reg(reg, value):
    bus.write_byte_data(MAX30102_ADDR, reg, value)

def read_fifo():
    data = bus.read_i2c_block_data(MAX30102_ADDR, REG_FIFO_DATA, 6)
    red = (data[0] << 16 | data[1] << 8 | data[2]) & 0x3FFFF
    ir = (data[3] << 16 | data[4] << 8 | data[5]) & 0x3FFFF
    return red, ir

def init_max30102():
    write_reg(REG_INTR_ENABLE_1, 0xC0)
    write_reg(REG_INTR_ENABLE_2, 0x00)
    write_reg(REG_FIFO_WR_PTR, 0x00)
    write_reg(REG_OVF_COUNTER, 0x00)
    write_reg(REG_FIFO_RD_PTR, 0x00)
    write_reg(REG_MODE_CONFIG, 0x03)
    write_reg(REG_SPO2_CONFIG, 0x27)
    write_reg(REG_LED1_PA, 0x24)
    write_reg(REG_LED2_PA, 0x24)

def bandpass_filter(data, fs, lowcut=0.7, highcut=3.5, order=2):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)

def measure_heart_rate(duration_sec=20, sample_rate=20):
    ir_data = []
    interval = 1.0 / sample_rate
    samples = int(duration_sec * sample_rate)
    print("正在采集数据，请保持手指贴紧传感器...")
    for _ in range(samples):
        _, ir = read_fifo()
        ir_data.append(ir)
        time.sleep(interval)
    ir_array = np.array(ir_data)
    filtered = bandpass_filter(ir_array, sample_rate)
    # 检测正峰和负峰
    peaks_pos, _ = find_peaks(filtered, distance=sample_rate*0.1, prominence=np.std(filtered)*0.04)
    peaks_neg, _ = find_peaks(-filtered, distance=sample_rate*0.1, prominence=np.std(filtered)*0.04)
    peaks = peaks_neg if len(peaks_neg) > len(peaks_pos) else peaks_pos
    if len(peaks) > 2:
        intervals = np.diff(peaks) / sample_rate
        valid = (intervals > 0.3) & (intervals < 2.0)
        valid_peaks = [peaks[0]] + [peaks[i+1] for i, v in enumerate(valid) if v]
        peak_count = len(valid_peaks)
    else:
        peak_count = len(peaks)
    heart_rate = (peak_count / duration_sec) * 60
    return heart_rate

if __name__ == "__main__":
    init_max30102()
    bpm = measure_heart_rate()
    print(f"测量心率：{bpm:.1f} 次/分钟")