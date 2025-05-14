import asyncio

import serial

# 打开串行端口
ser = serial.Serial('/dev/ttyUSB1', 256000, timeout=1)

async def radar(ws):
    while True:
        try:
            data = ser.read(7 * 11)
            length_list = [] # 索引0 运动1还是微动2 ，索引1，距离
            for i in range(len(data)):
                try:
                    if all((data[i] == 0xAA,data[i+1] == 0xAA,data[i+6] == 0x55,data[i+5] == 0x55)): # 第1,2位是AA
                        length = data[i+4]*256+data[i+3] # 小端
                        length_list.append(length)
                except IndexError:
                    pass
        # 过滤数据
        # print(length_list)
            length_list = sorted(length_list) # 排序
        # print(length_list)
        # 计算需要去除的元素数量
            remove_count = 3
            length_list = length_list[remove_count:-remove_count]
            length_ = sum(length_list) / len(length_list) if len(length_list) !=0 else 1
            await ws.send(length_)
        except asyncio.CancelledError:
            ser.close()
            raise

