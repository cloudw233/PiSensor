from gpiozero import PWMOutputDevice, DigitalOutputDevice
import time

# 简单的测试程序
def test_single_motor(en1_pin, en2_pin, pwm_pin):
    en1 = DigitalOutputDevice(en1_pin)
    en2 = DigitalOutputDevice(en2_pin)
    pwm = PWMOutputDevice(pwm_pin, frequency=1000, initial_value=0)
    
    try:
        print(f"测试引脚 EN1={en1_pin}, EN2={en2_pin}, PWM={pwm_pin}")
        # 设置方向
        en1.on()
        en2.off()
        # 逐步增加速度
        for speed in [0.3, 0.5, 0.7, 1.0]:
            print(f"速度: {speed*100}%")
            pwm.value = speed
            time.sleep(2)
    finally:
        en1.close()
        en2.close()
        pwm.close()

# 分别测试左右电机
test_single_motor(27, 22, 12)  # 测试左电机
time.sleep(2)
test_single_motor(23, 24, 13)  # 测试右电机