import gpiod
from periphery import PWM
from gpiod.line import Direction, Value
import time

class MotorControl:
    def __init__(self, ENL1, ENL2, ENR1, ENR2, pwmL, pwmR, chip='/dev/gpiochip0'):
        """
        初始化电机控制引脚。

        参数:
            ENL1 (int): 左侧电机使能引脚 1
            ENL2 (int): 左侧电机使能引脚 2
            ENR1 (int): 右侧电机使能引脚 1
            ENR2 (int): 右侧电机使能引脚 2
            pwmL (int): 左侧电机 PWM 引脚
            pwmR (int): 右侧电机 PWM 引脚
            chip (str): GPIO 芯片路径 (默认为 '/dev/gpiochip0')
        """
        self.ENL1 = ENL1
        self.ENL2 = ENL2
        self.ENR1 = ENR1
        self.ENR2 = ENR2
        self.pwmL = pwmL
        self.pwmR = pwmR
        self.chip_path = chip
        self.chip = gpiod.Chip(self.chip_path)

        # 定义引脚列表
        PINS = [ENL1, ENL2, ENR1, ENR2, pwmL, pwmR]

         # 创建配置
        config = {}
        for pin in PINS:
            config[pin] = gpiod.LineSettings(
                direction=Direction.OUTPUT,
                output_value=Value.INACTIVE
            )

       # 请求GPIO线路
        print("正在初始化GPIO...")
        try:
            self.lines = self.chip.request_lines(
                consumer="motor-control",
                config=config
            )
            print("GPIO初始化成功")
        except Exception as e:
            print(f"GPIO初始化失败: {e}")
            raise
        
    def control(self, direction):
        """
        控制电机运动方向。
        参数:
            direction (str): 'F' (前进), 'B' (后退), 'L' (左转), 'R' (右转)
        """
        try:
            # 降低 PWM 最大值为 100
            if direction == 'F':
                self._set_motor_state(1, 0, 1, 0, 100, 100)  # 前进
            elif direction == 'B':
                self._set_motor_state(0, 1, 0, 1, 100, 100)  # 后退
            elif direction == 'L':
                self._set_motor_state(1, 0, 1, 0, 40, 100)   # 左转
            elif direction == 'R':
                self._set_motor_state(1, 0, 1, 0, 100, 40)   # 右转
            else:
                print("无效的运动方向")
                return

            # 增加运行时间
            time.sleep(0.1)  # 延时100ms

            # 先降低 PWM，再关闭电机
            self._set_motor_state(1, 0, 1, 0, 0, 0)  # 先降低速度
            time.sleep(0.05)  # 等待电机减速
            self._set_motor_state(0, 0, 0, 0, 0, 0)  # 完全停止
            time.sleep(0.05)  # 等待电机完全停止
            
        except Exception as e:
            print(f"电机控制失败: {e}")
            # 发生异常时确保电机停止
            try:
                self._set_motor_state(0, 0, 0, 0, 0, 0)
            except:
                pass

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
        def stat(val:int):
            return Value.ACTIVE if bool(val) else Value.INACTIVE
        values = {self.ENL1: stat(ENL1_val), self.ENL2: stat(ENL2_val), self.ENR1: stat(ENR1_val),
                  self.ENR2: stat(ENR2_val), self.pwmL: pwmL_val, self.pwmR: pwmR_val}
        self.lines.set_values(values)

    def cleanup(self):
        """释放GPIO资源"""
        self.lines.release()
        self.chip.close()

if __name__ == '__main__':
    try:
        # 定义引脚 (根据实际连接修改)
        ENL1 = 27
        ENL2 = 22
        ENR1 = 23
        ENR2 = 24
        pwmL = 17
        pwmR = 18

        # 创建电机控制对象
        motor_control = MotorControl(ENL1, ENL2, ENR1, ENR2, pwmL, pwmR)

        # 控制电机前进
        print("前进...")
        motor_control.control('F')
        time.sleep(1)

        # 控制电机后退
        print("后退...")
        motor_control.control('B')
        time.sleep(1)

        # 控制电机左转
        print("左转...")
        motor_control.control('L')
        time.sleep(1)

        # 控制电机右转
        print("右转...")
        motor_control.control('R')
        time.sleep(1)

    except KeyboardInterrupt:
        print("程序终止")
    finally:
        if 'motor_control' in locals():
            motor_control.cleanup()