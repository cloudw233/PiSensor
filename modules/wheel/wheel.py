import time
from gpiozero import DigitalOutputDevice, PWMOutputDevice

class MotorControl:
    def __init__(self, ENL1, ENL2, ENR1, ENR2, pwmL, pwmR, pwm_freq=1000):
        """
        初始化电机控制
        :param ENL1,ENL2,ENR1,ENR2: 电机方向控制引脚(BCM编号)
        :param pwmL,pwmR: PWM速度控制引脚(BCM编号)
        :param pwm_freq: PWM频率(Hz)
        """
        # 电机方向控制引脚
        self.ENL1 = DigitalOutputDevice(ENL1)
        self.ENL2 = DigitalOutputDevice(ENL2)
        self.ENR1 = DigitalOutputDevice(ENR1)
        self.ENR2 = DigitalOutputDevice(ENR2)
        # PWM速度控制引脚
        self.pwmL = PWMOutputDevice(pwmL, frequency=pwm_freq, initial_value=0)
        self.pwmR = PWMOutputDevice(pwmR, frequency=pwm_freq, initial_value=0)

    def forward(self, speed=1.0):
        """
        前进
        :param speed: 速度(0.0~1.0)
        """
        self.ENL1.on()
        self.ENL2.off()
        self.ENR1.on()
        self.ENR2.off()
        self.pwmL.value = speed
        self.pwmR.value = speed

    def backward(self, speed=1.0):
        """
        后退
        :param speed: 速度(0.0~1.0)
        """
        self.ENL1.off()
        self.ENL2.on()
        self.ENR1.off()
        self.ENR2.on()
        self.pwmL.value = speed
        self.pwmR.value = speed

    def turn_left(self, speed=1.0):
        """
        左转
        :param speed: 速度(0.0~1.0)
        """
        self.ENL1.off()
        self.ENL2.on()
        self.ENR1.on()
        self.ENR2.off()
        self.pwmL.value = speed
        self.pwmR.value = speed

    def turn_right(self, speed=1.0):
        """
        右转
        :param speed: 速度(0.0~1.0)
        """
        self.ENL1.on()
        self.ENL2.off()
        self.ENR1.off()
        self.ENR2.on()
        self.pwmL.value = speed
        self.pwmR.value = speed

    def stop(self):
        """
        停止
        """
        self.ENL1.off()
        self.ENL2.off()
        self.ENR1.off()
        self.ENR2.off()
        self.pwmL.value = 0
        self.pwmR.value = 0

    def cleanup(self):
        """
        清理释放资源
        """
        self.stop()
        if self.ENL1.is_active: self.ENL1.close()
        if self.ENL2.is_active: self.ENL2.close()
        if self.ENR1.is_active: self.ENR1.close()
        if self.ENR2.is_active: self.ENR2.close()
        if self.pwmL.is_active: self.pwmL.close()
        if self.pwmR.is_active: self.pwmR.close()

if __name__ == '__main__':
    # 测试代码
    motor = MotorControl(
        ENL1=27, ENL2=22,  # 左电机方向控制引脚
        ENR1=23, ENR2=24,  # 右电机方向控制引脚
        pwmL=17, pwmR=18   # PWM速度控制引脚
    )
    
    try:
        for i in range(10):
            print("前进2秒")
            motor.forward(0.5)  # 50%速度前进
            time.sleep(2)
            
            print("后退2秒")
            motor.backward(0.5)  # 50%速度后退
            time.sleep(2)
            
            print("左转2秒")
            motor.turn_left(0.5)
            time.sleep(2)
            
            print("右转2秒")
            motor.turn_right(0.5)
            time.sleep(2)
        
        print("停止")
        motor.stop()
        
    finally:
        motor.cleanup()