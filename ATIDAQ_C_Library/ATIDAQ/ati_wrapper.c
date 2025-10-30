// ati_wrapper.c
// 轻量封装：把 ATI C 库的指针与数组调用变成易于 ctypes 调用的导出函数
// 构建为 atidaqft.dll

#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include "ftconfig.h"   // 确保包含路径正确：库自带头文件

#ifdef _WIN32
#define DLL_EXPORT __declspec(dllexport)
#else
#define DLL_EXPORT
#endif

// 用不透明句柄隐藏内部 Calibration*
typedef void* ATIFT_Handle;

DLL_EXPORT ATIFT_Handle atift_create(const char* calfile, uint16_t index) {
    Calibration* cal = createCalibration((char*)calfile, index);
    return (ATIFT_Handle)cal; // 失败返回 NULL
}

DLL_EXPORT void atift_destroy(ATIFT_Handle handle) {
    if (handle) destroyCalibration((Calibration*)handle);
}

DLL_EXPORT int16_t atift_set_force_units(ATIFT_Handle handle, const char* units) {
    if (!handle) return 1;
    return (int16_t)SetForceUnits((Calibration*)handle, (char*)units);
}

DLL_EXPORT int16_t atift_set_torque_units(ATIFT_Handle handle, const char* units) {
    if (!handle) return 1;
    return (int16_t)SetTorqueUnits((Calibration*)handle, (char*)units);
}

// 可选：设置工具坐标变换（平移单位和角度单位可选 "mm"/"in" 与 "degrees"/"radians"）
DLL_EXPORT int16_t atift_set_tool_transform(ATIFT_Handle handle,
                                            const double tt6[6],
                                            const char* dist_units,
                                            const char* angle_units) {
    if (!handle) return 1;
    float tf[6];
    for (int i = 0; i < 6; ++i) tf[i] = (float)tt6[i];
    return (int16_t)SetToolTransform((Calibration*)handle, tf, (char*)dist_units, (char*)angle_units);
}

// 置零：支持 6 或 7 通道（7 通道用于软件温补老传感器）
DLL_EXPORT void atift_bias6(ATIFT_Handle handle, const double v6[6]) {
    if (!handle) return;
    float bias[7];
    for (int i = 0; i < 6; ++i) bias[i] = (float)v6[i];
    bias[6] = 0.0f; // 硬件温补场景下热敏通道无意义
    Bias((Calibration*)handle, bias);
}

DLL_EXPORT void atift_bias7(ATIFT_Handle handle, const double v7[7]) {
    if (!handle) return;
    float bias[7];
    for (int i = 0; i < 7; ++i) bias[i] = (float)v7[i];
    Bias((Calibration*)handle, bias);
}

// 转换：6 通道输入（自动把第7通道填 0），返回 Fx,Fy,Fz,Tx,Ty,Tz（单位由 SetForceUnits/SetTorqueUnits 决定）
DLL_EXPORT void atift_convert6(ATIFT_Handle handle, const double v6[6], double out_ft[6]) {
    float in7[7], ft[6];
    for (int i = 0; i < 6; ++i) in7[i] = (float)v6[i];
    in7[6] = 0.0f;
    ConvertToFT((Calibration*)handle, in7, ft);
    for (int i = 0; i < 6; ++i) out_ft[i] = (double)ft[i];
}

// 转换：7 通道输入（用于软件温补）
DLL_EXPORT void atift_convert7(ATIFT_Handle handle, const double v7[7], double out_ft[6]) {
    float in7[7], ft[6];
    for (int i = 0; i < 7; ++i) in7[i] = (float)v7[i];
    ConvertToFT((Calibration*)handle, in7, ft);
    for (int i = 0; i < 6; ++i) out_ft[i] = (double)ft[i];
}
