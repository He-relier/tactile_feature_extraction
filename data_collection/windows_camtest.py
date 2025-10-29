import cv2

from pygrabber.dshow_graph import FilterGraph

def list_cameras():
    graph = FilterGraph()
    devices = graph.get_input_devices()  # 返回设备友好名列表
    for i, name in enumerate(devices):
        print(f"[{i}] {name}")
    return devices

def open_camera(index=3, width=640, height=480):
    # 打开摄像头
    cam = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # Windows 推荐 CAP_DSHOW
    if not cam.isOpened():
        raise RuntimeError(f"无法打开摄像头 {index}")

    # ===================== 分辨率设置 =====================
    cam.set(3, width)   # CAP_PROP_FRAME_WIDTH
    cam.set(4, height)  # CAP_PROP_FRAME_HEIGHT

    # ===================== 曝光设置 =====================
    # 注：不同相机厂商曝光控制方式不同，某些驱动需要关闭自动曝光才可手动设值。
    # 若不生效，可尝试 cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) 或 0。
    cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)     # 开启自动曝光（1=自动，0=手动）
    cam.set(cv2.CAP_PROP_EXPOSURE, 312.5)      # 设置曝光值（仅部分驱动支持）

    # ===================== 亮度设置 =====================
    cam.set(cv2.CAP_PROP_BRIGHTNESS, 64)       # 设置亮度（范围依设备而定）

    # 打印实际参数（方便调试）
    print("当前设置：")
    print("宽度：", cam.get(3))
    print("高度：", cam.get(4))
    print("曝光：", cam.get(cv2.CAP_PROP_EXPOSURE))
    print("亮度：", cam.get(cv2.CAP_PROP_BRIGHTNESS))

    return cam


def main():
    x=list_cameras()
    print(x)
    cam = open_camera(index=1, width=640, height=480)
    print("按 q 退出，按 s 保存图像。")

    while True:
        ok, frame = cam.read()
        if not ok:
            print("无法读取帧。")
            break

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite("frame.jpg", frame)
            print("已保存 frame.jpg")

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
