# atift_runtime.py —— 启动自动归零 + 手动归零（Z）
import ctypes as C
from ctypes import c_double, c_uint16, c_char_p, c_void_p, c_int16
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import msvcrt, os, time
import statistics

# 1) DLL 路径（按你的实际情况）
os.add_dll_directory(r"E:\ATI_force\ATIDAQ C Library\ATIDAQ")
lib = C.cdll.LoadLibrary(r"E:\ATI_force\ATIDAQ C Library\ATIDAQ\atidaqft.dll")

# 2) 函数签名
lib.atift_create.restype = c_void_p
lib.atift_create.argtypes = [c_char_p, c_uint16]
lib.atift_destroy.argtypes = [c_void_p]
lib.atift_set_force_units.restype = c_int16
lib.atift_set_force_units.argtypes = [c_void_p, c_char_p]
lib.atift_set_torque_units.restype = c_int16
lib.atift_set_torque_units.argtypes = [c_void_p, c_char_p]
lib.atift_bias6.argtypes = [c_void_p, C.POINTER(c_double)]
lib.atift_convert6.argtypes = [c_void_p, C.POINTER(c_double), C.POINTER(c_double)]

# 3) 载入标定
CAL_FILE = r"E:\ATI_force\tactile_feature_extraction\FT39618.cal"  # ← 改成你的 .cal
cal = lib.atift_create(C.c_char_p(CAL_FILE.encode('utf-8')), 1)
if not cal:
    raise RuntimeError("加载 ATI 校准文件失败")

# （可选）统一单位为 SI
if lib.atift_set_force_units(cal, b"N") != 0:  raise RuntimeError("SetForceUnits 失败")
if lib.atift_set_torque_units(cal, b"N-m") != 0:  raise RuntimeError("SetTorqueUnits 失败")

channels = [f"Dev1/ai{i}" for i in range(6)]
print("启动后将自动归零。按 'Z' 可随时手动归零，按 'Q' 退出。")

def do_bias_from_volts(volts6):
    """把 6 路电压作为偏置传给库，完成归零。"""
    v_arr = (c_double * 6)(*map(float, volts6))
    lib.atift_bias6(cal, v_arr)

def auto_bias(task, samples=200, settle_s=0.3):
    """
    启动自动归零：
    - 等待 settle_s 让放大器和信号稳定（手不要碰传感器）
    - 采 samples 帧电压求均值作为偏置
    """
    print(f"[AUTO BIAS] 请保持传感器无载荷，{settle_s}s 后开始采样 {samples} 帧…")
    time.sleep(settle_s)
    buf = []
    for _ in range(samples):
        buf.append(task.read())  # list 长度=6
    # 对每个通道取均值
    means = [statistics.fmean(ch) for ch in zip(*buf)]
    do_bias_from_volts(means)
    print("[AUTO BIAS] 完成，偏置(V) =", [f"{x:.5f}" for x in means])

# with nidaqmx.Task() as task:
task= nidaqmx.Task()        
for ch in channels:
    task.ai_channels.add_ai_voltage_chan(
        ch,
        terminal_config=TerminalConfiguration.RSE,
        min_val=0.0, max_val=5.0
    )

# —— 新增：启动自动归零 ——
auto_bias(task, samples=200, settle_s=0.5)

while True:
    # 键盘：Z 手动归零，Q 退出
    if msvcrt.kbhit():
        key = msvcrt.getch().decode(errors='ignore').lower()
        if key == 'q':
            break
        if key == 'z':
            # 取若干帧均值做手动归零
            buf = [task.read() for _ in range(60)]
            means = [statistics.fmean(ch) for ch in zip(*buf)]
            do_bias_from_volts(means)
            print("[BIAS] 手动归零完成，偏置(V) =", [f"{x:.5f}" for x in means])

    # 采一帧 → 转换为力矩
    v = task.read()                 # 6 路电压
    v_arr = (c_double * 6)(*map(float, v))
    out = (c_double * 6)()
    lib.atift_convert6(cal, v_arr, out)
    ft = [out[i] for i in range(6)]
    print(" FT:", " ".join(f"{x:8.3f}" for x in ft))

lib.atift_destroy(cal)
print("Done.")
