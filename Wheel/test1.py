import time
import gpiod
from gpiod.line import Direction, Value
import sys
import glob

class MotorControl:
    def __init__(self, chip_path, pin_numbers):
        try:
            # 使用完整路径打开GPIO芯片
            self.chip = gpiod.Chip(chip_path)
            self.pin_map = pin_numbers
            self.motor_pins = pin_numbers

            # 创建线路配置
            line_settings = gpiod.LineSettings(
                direction=Direction.OUTPUT,
                output_value=Value.INACTIVE
            )
            
            # 请求GPIO线路
            pin_values = list(pin_numbers.values())
            config={pin: line_settings for pin in self.motor_pins.values()}

            self.request = self.chip.request_lines(
                consumer="wheel-motor",
                config=config
            )
            print(f"成功配置GPIO引脚: {pin_numbers}")
            
        except Exception as e:
            print(f"初始化底盘电机失败: {e}", file=sys.stderr)
            raise

    # def control(self, direction):
    #     """
    #     控制电机运动方向。
    #     参数:
    #         direction (str): 'F' (前进), 'B' (后退), 'L' (左转), 'R' (右转)
    #     """
    #     try:
    #         # 降低 PWM 最大值为 100
    #         if direction == 'F':
    #             self._set_motor_state(1, 0, 1, 0, 100, 100)  # 前进
    #         elif direction == 'B':
    #             self._set_motor_state(0, 1, 0, 1, 100, 100)  # 后退
    #         elif direction == 'L':
    #             self._set_motor_state(1, 0, 1, 0, 40, 100)   # 左转
    #         elif direction == 'R':
    #             self._set_motor_state(1, 0, 1, 0, 100, 40)   # 右转
    #         else:
    #             print("无效的运动方向")
    #             return

    #         # 增加运行时间
    #         time.sleep(0.1)  # 延时100ms

    #         # 先降低 PWM，再关闭电机
    #         self._set_motor_state(1, 0, 1, 0, 0, 0)  # 先降低速度
    #         time.sleep(0.05)  # 等待电机减速
    #         self._set_motor_state(0, 0, 0, 0, 0, 0)  # 完全停止
    #         time.sleep(0.05)  # 等待电机完全停止
            
    #     except Exception as e:
    #         print(f"电机控制失败: {e}")
    #         # 发生异常时确保电机停止
    #         try:
    #             self._set_motor_state(0, 0, 0, 0, 0, 0)
    #         except:
    #             pass

    def control(self, direction):
        try:
            if direction == 'F':
                # 使用实际的引脚号码
                values = {
                    self.pin_map['ENL1']: Value.ACTIVE,
                    self.pin_map['ENL2']: Value.INACTIVE,
                    self.pin_map['ENR1']: Value.ACTIVE,
                    self.pin_map['ENR2']: Value.INACTIVE,
                    self.pin_map['pwmL']: 200,
                    self.pin_map['pwmR']: 200
                }
            elif direction == 'B':
                values = {
                    self.pin_map['ENL1']: Value.INACTIVE,
                    self.pin_map['ENL2']: Value.ACTIVE,
                    self.pin_map['ENR1']: Value.INACTIVE,
                    self.pin_map['ENR2']: Value.ACTIVE,
                    self.pin_map['pwmL']: 200,
                    self.pin_map['pwmR']: 200
                }
            self.request.set_values({pin: values[pin] for pin in self.request.offsets})
        except Exception as e:
            print(f"控制失败: {e}")


    def _set_motor_state(self, ENL1_val, ENL2_val, ENR1_val, ENR2_val, pwmL_val, pwmR_val):
        """
        设置电机状态。

        参数:
            ENL1_val (int): ENL1 引脚状态 (0 或 1)
            ENL2_val (int): ENL2 引脚状态 (0 或 1)
            ENR1_val (int): ENR1 引脚状态 (0 或 1)
            ENR2_val (int): ENR2 引脚状态 (0 或 1)
            pwmL_val (int): 左侧电机 PWM 值 (0-255)
            pwmR_val (int): 右侧电机 PWM 值 (0-255)
        """
        # 设置数字引脚状态
        values = {self.ENL1: ENL1_val, self.ENL2: ENL2_val, self.ENR1: ENR1_val,
                  self.ENR2: ENR2_val, self.pwmL: pwmL_val, self.pwmR: pwmR_val}
        self.lines.set_values(values)

    def cleanup(self):
        if hasattr(self, 'request'):
            self.request.release()
        if hasattr(self, 'chip'):
            self.chip.close()        
    
    def release(self):
        """释放GPIO资源"""
        if hasattr(self, 'request'):
            self.request.release()
        if hasattr(self, 'chip'):
            self.chip.close()

if __name__ == "__main__":
    
    ENL1 = 27
    ENL2 = 22
    ENR1 = 23
    ENR2 = 24
    pwmL = 17
    pwmR = 18
    
    pin_numbers = {
        'ENL1': 27,
        'ENL2': 22,
        'ENR1': 23,
        'ENR2': 24,
        'pwmL': 17,
        'pwmR': 18
    }

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
        motor_control = MotorControl("/dev/gpiochip0", pin_numbers = pin_numbers)

        # 控制电机前进
        print("前进...")
        motor_control.control('F')
        time.sleep(1)

        # 控制电机后退
        print("后退...")
        motor_control.control('B')
        time.sleep(1)

        # # 控制电机左转
        # print("左转...")
        # motor_control.control('L')
        # time.sleep(1)

        # # 控制电机右转
        # print("右转...")
        # motor_control.control('R')
        # time.sleep(1)

    except KeyboardInterrupt:
        print("程序终止")
    finally:
        if 'motor_control' in locals():
            motor_control.cleanup()
        time.sleep(1)
        
        print("done")
        
