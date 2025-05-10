import time
import gpiod
from gpiod.line import Direction, Value
import sys
import glob

class StepperMotor:
    def __init__(self, chip_path, pin_numbers):
        try:
            # 使用完整路径打开GPIO芯片
            self.chip = gpiod.Chip(chip_path)
            chip_info = self.chip.get_info()
            # print(f"成功打开GPIO芯片: {chip_info.name}")
            # print(f"GPIO芯片信息: {chip_info.name}, 引脚数量: {chip_info.num_lines}")
            
            # if any(pin >= chip_info.num_lines for pin in pin_numbers):
            #     raise ValueError(f"无效的引脚号: {pin_numbers}")
            
            # 创建线路配置
            line_settings = gpiod.LineSettings(
                direction=Direction.OUTPUT,
                output_value=Value.INACTIVE
            )
            
            # 请求GPIO线路
            self.request = self.chip.request_lines(
                consumer="stepper-motor",
                config={pin: line_settings for pin in pin_numbers}
            )
            # print(f"成功配置GPIO引脚: {pin_numbers}")
            
            # 初始化相位序列（八拍模式）
            self.phase_sequence = [
                [Value.ACTIVE, Value.INACTIVE, Value.INACTIVE, Value.INACTIVE],
                [Value.ACTIVE, Value.ACTIVE, Value.INACTIVE, Value.INACTIVE],
                [Value.INACTIVE, Value.ACTIVE, Value.INACTIVE, Value.INACTIVE],
                [Value.INACTIVE, Value.ACTIVE, Value.ACTIVE, Value.INACTIVE],
                [Value.INACTIVE, Value.INACTIVE, Value.ACTIVE, Value.INACTIVE],
                [Value.INACTIVE, Value.INACTIVE, Value.ACTIVE, Value.ACTIVE],
                [Value.INACTIVE, Value.INACTIVE, Value.INACTIVE, Value.ACTIVE],
                [Value.ACTIVE, Value.INACTIVE, Value.INACTIVE, Value.ACTIVE]
            ]
            self.current_step = 0
            
        except Exception as e:
            print(f"初始化步进电机失败: {e}", file=sys.stderr)
            raise

    def step(self, direction="cw", delay_ms=2):
        """执行单步转动"""
        if direction == "cw":
            self.current_step = (self.current_step + 1) % 8
        elif direction == "ccw":
            self.current_step = (self.current_step - 1) % 8
        
        # 获取当前步骤的相位值
        phase_values = self.phase_sequence[self.current_step]
        
        # 将相位值写入GPIO引脚
        values_dict = {pin: value for pin, value in zip(self.request.offsets, phase_values)}
        self.request.set_values(values_dict)
        
        # 延时
        time.sleep(delay_ms / 1000.0)

    def rotate(self, steps, direction="cw", delay_ms=2):
        """旋转指定步数
        
        参数:
            steps: 需要旋转的步数
            direction: 旋转方向，"cw"顺时针，"ccw"逆时针
            delay_ms: 每步之间的延时（毫秒）
        """
        for _ in range(steps):
            self.step(direction, delay_ms)
    
    def release(self):
        """释放GPIO资源"""
        if hasattr(self, 'request'):
            self.request.release()
        if hasattr(self, 'chip'):
            self.chip.close()

if __name__ == "__main__":
    MOTOR_PINS1 = [21, 26, 20, 19]  # 根据实际连接修改
    MOTOR_PINS2 = [13, 6, 5, 0]

    
    try:
        print("正在检查可用的GPIO芯片...")
        gpio_chips = glob.glob('/dev/gpiochip*')
        available_chips = []
        
        for chip_path in gpio_chips:
            try:
                with gpiod.Chip(chip_path) as chip:
                    chip_info = chip.get_info()
                    # print(f"发现GPIO芯片: {chip_info.name}, 引脚数量: {chip_info.num_lines}")
                    available_chips.append(chip_path)
            except Exception as e:
                print(f"无法访问 {chip_path}: {e}")
        
        # if not available_chips:
        #     raise RuntimeError("未找到可用的GPIO芯片")
            
        # 使用完整路径创建电机对象
        motor1 = StepperMotor("/dev/gpiochip0", MOTOR_PINS1)
        motor2 = StepperMotor("/dev/gpiochip0", MOTOR_PINS2)
        
        
        motor1.rotate(4096, "cw", delay_ms=3)
        motor2.rotate(4096, "cw", delay_ms=3)
        time.sleep(1)
        
        
        motor1.rotate(2048, "ccw", delay_ms=1)
        motor2.rotate(2048, "ccw", delay_ms=1)
        
        print("done")
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
    finally:
        if 'motor1' and 'motor2' in locals():
            motor1.release()
            motor2.release()
            print("已释放GPIO资源")