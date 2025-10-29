import cv2

# 打开摄像头（0 表示第一个摄像头，可改成 1、2）
cam = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# ---------------------------
# # 基础设置：分辨率
cam.set(3, 640)   # 宽度 (cv2.CAP_PROP_FRAME_WIDTH)
cam.set(4, 480)   # 高度 (cv2.CAP_PROP_FRAME_HEIGHT)

# # ---------------------------
# # 曝光设置
# # 注意：不同摄像头的驱动对曝光值的解释不同（有的用负数，有的用 0~1）
# # 一般流程是先关闭自动曝光，再手动设置曝光值
# cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)   # 1=手动模式，3=自动模式（某些驱动是 0.25/0.75）
cam.set(cv2.CAP_PROP_EXPOSURE, -5)    # 曝光值，数值越大画面越亮
cam.set(cv2.CAP_PROP_FPS, 30)

# # ---------------------------
# # 亮度设置
cam.set(cv2.CAP_PROP_BRIGHTNESS, 64)

# ---------------------------
# 读取并显示画面
while True:
    ret, frame = cam.read()
    if not ret:
        print("无法读取摄像头画面")
        break
    cv2.imshow("Camera", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # 按 Q 退出
        break

cam.release()
cv2.destroyAllWindows()
