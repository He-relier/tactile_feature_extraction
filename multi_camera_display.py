import cv2
import threading
import time
import numpy as np

class MultiCameraCapture:
    def __init__(self, camera_sources):
        self.camera_sources = camera_sources
        self.captures = [cv2.VideoCapture(src) for src in camera_sources]
        self.setup_camera()
        self.threads = []
        self.frames = [None for _ in camera_sources]
        self.active = True
        self.frame_times = [0 for _ in camera_sources]
        self.last_time = [time.time() for _ in camera_sources]
        self.lock_race = threading.Lock()

    def setup_camera(self,):
        for i in range(len(self.captures)):
            # Exposure mode
            flag = self.captures[i].set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            print('Set auto exposure mode, ',flag)
            # Resolution
            flag = self.captures[i].set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            flag = self.captures[i].set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            print('Set resolution for camera {}, {}'.format(self.camera_sources[i], flag))
            # Exposure
            flag = self.captures[i].set(cv2.CAP_PROP_EXPOSURE, 312.5)
            print('Set exposure for camera {}, {}'.format(self.camera_sources[i], flag))
            # Brightness
            flag = self.captures[i].set(cv2.CAP_PROP_BRIGHTNESS, 64)
            print('Set brightness, ',flag)

    def _capture_camera(self, cap, index):
        while self.active:
            start_time = time.time()
            ret, frame = cap.read()
            elapsed_time = time.time() - start_time

            # Process frame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = frame[..., np.newaxis]
            
            # Update frame times to calculate FPS
            self.frame_times[index] += elapsed_time
            if self.frame_times[index] >= 1:  # recalculate FPS once every second
                fps = 1 / elapsed_time
                frame = cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                self.frame_times[index] %= 1
            else:
                last_fps = 1 / (elapsed_time or 1e-6)
                frame = cv2.putText(frame, f"FPS: {last_fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        
            self.frames[index] = frame

        cap.release()

    def start(self):
        for i, cap in enumerate(self.captures):
            thread = threading.Thread(target=self._capture_camera, args=(cap, i))
            thread.start()
            self.threads.append(thread)

    def display(self):
        while True:
            for i, frame in enumerate(self.frames):
                if frame is not None:
                    cv2.imshow(f"Camera {self.camera_sources[i]}", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.active = False
                break

    def wait(self):
        for thread in self.threads:
            thread.join()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    camera_sources = [10,12,14,8]
    multi_cam = MultiCameraCapture(camera_sources)
    multi_cam.start()
    multi_cam.display()
    multi_cam.wait()
