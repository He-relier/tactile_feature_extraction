# atift_runtime.py
import ctypes as C
from ctypes import c_double, c_uint16, c_char_p, c_void_p, c_int16
import numpy as np
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import msvcrt  # Windows 下用来非阻塞键盘检测

# 1) 加载 DLL
lib = C.cdll.LoadLibrary(r"E:\ATI_force\ATIDAQ_C_Library\ATIDAQ\atidaqft.dll")


# 2) 声明函数签名
lib.atift_create.restype = c_void_p
lib.atift_create.argtypes = [c_char_p, c_uint16]

lib.atift_destroy.restype = None
lib.atift_destroy.argtypes = [c_void_p]

lib.atift_set_force_units.restype = c_int16
lib.atift_set_force_units.argtypes = [c_void_p, c_char_p]

lib.atift_set_torque_units.restype = c_int16
lib.atift_set_torque_units.argtypes = [c_void_p, c_char_p]

lib.atift_set_tool_transform.restype = c_int16
lib.atift_set_tool_transform.argtypes = [c_void_p,
                                         C.POINTER(c_double), c_char_p, c_char_p]

lib.atift_bias6.restype = None
lib.atift_bias6.argtypes = [c_void_p, C.POINTER(c_double)]

lib.atift_convert6.restype = None
lib.atift_convert6.argtypes = [c_void_p, C.POINTER(c_double), C.POINTER(c_double)]

# 3) 创建校准
CAL_FILE = r"E:\ATI_force\tactile_feature_extraction\FT39618.cal"  # ← 替换为你的 .cal 文件
cal = lib.atift_create(C.c_char_p(CAL_FILE.encode('utf-8')), 1)
if not cal:
    raise RuntimeError("Failed to load ATI calibration file")

# 可选：设单位（也可注释掉靠标定文件默认）
if lib.atift_set_force_units(cal, b"N") != 0:
    raise RuntimeError("SetForceUnits failed")
if lib.atift_set_torque_units(cal, b"N-m") != 0:
    raise RuntimeError("SetTorqueUnits failed")

# 可选：设置工具坐标变换（平移单位 mm、角度单位 degrees）
# tt = (c_double * 6)(0, 0, 0, 0, 0, 0)  # 不需要就设零变换
# if lib.atift_set_tool_transform(cal, tt, b"mm", b"degrees") != 0:
#     raise RuntimeError("SetToolTransform failed")

# 4) 准备 NI-DAQ 采集
channels = [f"Dev1/ai{i}" for i in range(6)]  # 按你实际接线修改
print("Press 'Z' to ZERO (Bias). Press 'Q' to quit.")

bias_done = False

with nidaqmx.Task() as task:
    for ch in channels:
        task.ai_channels.add_ai_voltage_chan(
            ch,
            terminal_config=TerminalConfiguration.RSE,
            min_val=0.0, max_val=5.0
        )

    while True:
        # 键盘检测
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
            if key == 'q':
                break
            elif key == 'z':
                # 读取一次作为置零
                v = task.read()  # list of 6 floats
                v_arr = (c_double * 6)(*map(float, v))
                lib.atift_bias6(cal, v_arr)
                bias_done = True
                print("[BIAS] Zeroed at current reading:", ["%.4f" % x for x in v])

        # 读一次电压并转换
        volts = task.read()  # 6 floats
        v_arr = (c_double * 6)(*map(float, volts))
        out = (c_double * 6)()
        lib.atift_convert6(cal, v_arr, out)
        ft = [out[i] for i in range(6)]

        # 注意：Fx,Fy,Fz,Tx,Ty,Tz 的符号/方向由传感器坐标系与标定文件定义
        print("V:", " ".join(f"{x:7.4f}" for x in volts),
              " | FT:", " ".join(f"{x:8.3f}" for x in ft),
              (" (BIAS SET)" if bias_done else ""))

# 5) 清理
lib.atift_destroy(cal)
print("Done.")
