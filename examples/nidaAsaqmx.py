import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import time

# 1) 创建任务
with nidaqmx.Task() as task:
    # 2) 添加 6 路模拟输入通道（根据你的实际接线修改）
    channels = [f"Dev1/ai{i}" for i in range(6)]
    for ch in channels:
        task.ai_channels.add_ai_voltage_chan(
            ch,
            terminal_config=TerminalConfiguration.RSE,  # 单端输入 (RSE)
            min_val=0.0,    # 最小电压，根据你的放大器设置调整
            max_val=5.0     # 最大电压
        )

    print(f"Reading {len(channels)} channels: {', '.join(channels)}")
    print("Press Ctrl+C to stop...\n")

    # 3) 连续读取
    try:
        while True:
            # 一次读取所有通道的瞬时电压
            voltages = task.read()  # 返回一个包含6个浮点数的列表
            # 打印输出
            voltage_str = "  ".join([f"ai{i}: {v:.4f} V" for i, v in enumerate(voltages)])
            print(voltage_str)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped by user.")
"FZ,FY,FX,TZ,TY,TX"