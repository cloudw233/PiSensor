import time
from gpiozero import DigitalOutputDevice


class StepperMotor:
    def __init__(self, pin1, pin2, pin3, pin4):
        """
        初始化步进电机。

        参数:
            pin1, pin2, pin3, pin4: 连接到步进电机控制器的GPIO引脚（BCM编号）。
        """
        self.coil_1A = DigitalOutputDevice(pin1)
        self.coil_1B = DigitalOutputDevice(pin2)
        self.coil_2A = DigitalOutputDevice(pin3)
        self.coil_2B = DigitalOutputDevice(pin4)

        # 相位序列（全步模式）
        self.full_step_sequence = [
                [1, 0, 0, 0],
                [1, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 1],
                [0, 0, 0, 1],
                [1, 0, 0, 1]
            ]

        self.current_step = 0

    def step(self, direction="cw", delay=0.0015):
        """
        执行一步。

        参数:
            direction: "cw" 表示顺时针，"ccw" 表示逆时针。
            delay: 步进之间的延迟（秒）。
        """
        if direction == "cw":
            self.current_step = (self.current_step + 1) % 8
        else:
            self.current_step = (self.current_step - 1) % 8

        self.set_coil_state(self.full_step_sequence[self.current_step])
        time.sleep(delay)

    def rotate(self, steps, direction="cw", delay=0.0015):
        """
        旋转指定的步数。

        参数:
            steps: 要执行的步数。
            direction: "cw" 表示顺时针，"ccw" 表示逆时针。
            delay: 步进之间的延迟（秒）。
        """
        for _ in range(steps):
            self.step(direction, delay)

    def set_coil_state(self, state):
        """
        设置线圈的状态。

        参数:
            state: 一个包含四个值的列表，表示线圈的状态（1 表示激活，0 表示未激活）。
        """
        self.coil_1A.value = state[0]
        self.coil_1B.value = state[1]
        self.coil_2A.value = state[2]
        self.coil_2B.value = state[3]

    def release(self):
        """
        释放GPIO资源。
        """
        self.coil_1A.close()
        self.coil_1B.close()
        self.coil_2A.close()
        self.coil_2B.close()


if __name__ == '__main__':
    # 定义连接到步进电机的GPIO引脚
    MOTOR_PINS1 = [21, 26, 20, 19]  # 根据实际连接修改
    MOTOR_PINS2 = [13, 6, 5, 0]

    try:
        # 创建两个步进电机对象
        motor1 = StepperMotor(*MOTOR_PINS1)
        motor2 = StepperMotor(*MOTOR_PINS2)

        motor1.rotate(512, direction='cw')
        motor1.rotate(512, direction='ccw')
        time.sleep(1)
        motor2.rotate(512, direction='cw')
        motor2.rotate(512, direction='ccw')

        print("Done")

    finally:
        # 释放GPIO资源
        motor1.release()
        motor2.release()
        print("GPIO resources released")