# import RPi.GPIO as GPIO
# import time

# # 引脚定义 (BCM编号)
# IN1, IN2, IN3, IN4 = 17, 18, 22, 23
# GPIO.setmode(GPIO.BCM)
# GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)

# # 4相8拍步进顺序 (28BYJ-48)
# sequence = [
#     [1, 0, 0, 1],  # 步1
#     [1, 0, 0, 0],   # 步2
#     [1, 1, 0, 0],   # 步3
#     [0, 1, 0, 0],   # 步4
#     [0, 1, 1, 0],   # 步5
#     [0, 0, 1, 0],   # 步6
#     [0, 0, 1, 1],   # 步7
#     [0, 0, 0, 1]    # 步8
# ]

# try:
#     print("按Ctrl+C停止")
#     while True:
#         for step in sequence:
#             GPIO.output(IN1, step[0])
#             GPIO.output(IN2, step[1])
#             GPIO.output(IN3, step[2])
#             GPIO.output(IN4, step[3])
#             time.sleep(0.001)  # 调整延时控制转速
# except KeyboardInterrupt:
#     GPIO.cleanup()
#     print("程序终止")

import gpiod
import time

def init_gpio():
    """初始化GPIO设备"""
    try:
        # 获取GPIO芯片
        chip = gpiod.Chip('gpiochip0')
        
        # 定义引脚 (BCM编号)
        PINS = [17, 18, 22, 23]  # IN1, IN2, IN3, IN4
        
        # 使用单独的line请求替代get_lines
        lines = []
        for pin in PINS:
            line = chip.get_line(pin)
            line.request(consumer="stepper", type=gpiod.LINE_REQ_DIR_OUT)
            lines.append(line)
        
        return chip, lines
    except Exception as e:
        print(f"GPIO初始化失败: {e}")
        return None, None

def step_motor(lines, steps, delay=0.001):
    """控制步进电机转动"""
    sequence = [
        [1, 0, 0, 1],
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1]
    ]
    
    try:
        for _ in range(abs(steps)):
            for step in (sequence if steps > 0 else reversed(sequence)):
                # 逐个设置引脚状态
                for line, value in zip(lines, step):
                    line.set_value(value)
                time.sleep(delay)
    except KeyboardInterrupt:
        print("\n程序终止")
        for line in lines:
            line.set_value(0)

def main():
    chip, lines = init_gpio()
    if not lines:
        return
        
    try:
        while True:
            step_motor(lines, 512)  # 正转一圈
            time.sleep(1)
            step_motor(lines, -512)  # 反转一圈
            time.sleep(1)
    finally:
        if lines:
            for line in lines:
                line.set_value(0)
        if chip:
            chip.close()

if __name__ == "__main__":
    main()