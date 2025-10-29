import cv2
import pickle 
import Pyro4
import os
import time
import socket, struct
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from time import sleep
#from tactile_feature_extraction.utils.utils_ft_sensor import Sensor

#for mini45 FT sensor
#=============================
import ctypes as C
from ctypes import c_double, c_uint16, c_char_p, c_void_p, c_int16
import nidaqmx
from nidaqmx.constants import TerminalConfiguration
#=============================

from threading import Thread, Lock

class DataGatherer_45(object):
	def __init__(self, resume, dataPath, time_series, display_image,resize):
		self.resize = resize
		# FT Sensor inits:
		self.mean = [0] * 6
		self.stream = False
		self.newtons_data = None

		# Path inits:
		self.dataPath = dataPath
		self.time_series = time_series 
		self.display_image = display_image

		if resume == False:
			frame_folder = os.path.join(self.dataPath, f'raw_frames')
			os.makedirs(frame_folder, exist_ok=True)

			video_folder = os.path.join(self.dataPath, f'videos')
			os.makedirs(video_folder, exist_ok=True)

			timeseries_folder = os.path.join(self.dataPath, f'time_series')
			os.makedirs(timeseries_folder, exist_ok=True)

		self.framePath = f'{self.dataPath}/raw_frames'
		self.videoPath = f'{self.dataPath}/videos'
		self.timeseriesPath = f'{self.dataPath}/time_series'

		self.Fx = None
		self.Fy = None
		self.Fz = None

		self.Fx_list = []
		self.Fy_list = []
		self.Fz_list = []

		# TacTip inits:
		# Port
		self.cam = cv2.VideoCapture(0)################################################cam
		if not self.cam.isOpened():
			raise SystemExit("Error: Could not open camera.")
		else:
			print("Camera opened successfully.")

		# Resolution
		self.cam.set(3, 640)
		self.cam.set(4, 480)

		# Exposure
		self.cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
		self.cam.set(cv2.CAP_PROP_EXPOSURE, -5)
		# Brightness
		self.cam.set(cv2.CAP_PROP_BRIGHTNESS, 64)

		self.frame = None
		self.cam_ready = False
		self.i = None

		# Sampling inits:
		self.sample = 0 # Sample number
		self.sample_list = []
		
		self.start_time = time.time()
		self.out = None

		self.t = []

		self.threadRun = False
		self.log = False


		#for mini45 FT sensor
		#=============================
		self._dll_path  = r"E:\ATI_force\ATIDAQ C Library\ATIDAQ\atidaqft.dll"
		self._cal_file  = r"E:\ATI_force\tactile_feature_extraction\FT39618.cal"  

		self._lib = C.cdll.LoadLibrary(self._dll_path)
		self._lib.atift_create.restype = c_void_p
		self._lib.atift_create.argtypes = [c_char_p, c_uint16]
		self._lib.atift_destroy.argtypes = [c_void_p]
		self._lib.atift_set_force_units.restype = c_int16
		self._lib.atift_set_force_units.argtypes = [c_void_p, c_char_p]
		self._lib.atift_set_torque_units.restype = c_int16
		self._lib.atift_set_torque_units.argtypes = [c_void_p, c_char_p]
		self._lib.atift_bias6.argtypes = [c_void_p, C.POINTER(c_double)]
		self._lib.atift_convert6.argtypes = [c_void_p, C.POINTER(c_double), C.POINTER(c_double)]
 # 3) 创建校准（index 常用 1），单位统一为 SI
		self._cal = self._lib.atift_create(c_char_p(self._cal_file.encode('utf-8')), 1)
		if not self._cal:
			raise RuntimeError("加载 ATI 校准文件失败")
		if self._lib.atift_set_force_units(self._cal, b"N") != 0:
			raise RuntimeError("SetForceUnits 失败")
		if self._lib.atift_set_torque_units(self._cal, b"N-m") != 0:
			raise RuntimeError("SetTorqueUnits 失败")

		# 4) NI-DAQ 任务（按你的接线修改通道/接法/量程）
		self._ai_channels = [f"Dev1/ai{i}" for i in range(6)]
		self._ai_termconf = TerminalConfiguration.RSE   # 差分则改为 TerminalConfiguration.DIFF
		self._vmin, self._vmax = 0.0, 5.0              # ±10V 放大器就改成 -10.0, 10.0
		self._ai_task = nidaqmx.Task()
		for ch in self._ai_channels:
			self._ai_task.ai_channels.add_ai_voltage_chan(
				ch, terminal_config=self._ai_termconf, min_val=self._vmin, max_val=self._vmax
			)

		# 5) DLL 置零状态
		self._biased = False
	

	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		print('exiting...')
		self.close()

	def start(self):
		self.tare(n=1000) # Calibrate sensor

		# Start main data logging threads:
		self.imageThread = Thread(None, self.image_worker, daemon=True) 
		self.startStreaming() # Starts FT stream
		self.threadRun = True
		print(f'self.threadRun {self.threadRun}')
		self.imageThread.start() # Starts camera stream
		
		time.sleep(1)

	def begin_sample(self, i):
		''' Begins a new sample by making a directory for video data
			according to the sample number.
		'''
		self.i = i
		video_folder = os.path.join(self.videoPath, f'sample_{self.i}')
		os.makedirs(video_folder, exist_ok=True)
		self.videoframesPath = video_folder
		self.log = True
	
	def avg_force(self, data, t):
		''' Calculates the average force per frame for a given sample 
		    and returns as a dictionary.
		'''
		# Transpose the input data to match the expected format for DataFrame creation
		n, fx, fy, fz = data
		structured_data = list(zip(n, fx, fy, fz))
		
		# Create a DataFrame from the structured data
		df = pd.DataFrame(structured_data, columns=['frame', 'fx', 'fy', 'fz'])
		
		# Compute the mean values of fx, fy, fz for each value of n
		mean_df = df.groupby('frame').mean().reset_index()
	
		# Adjust the length of t to match the length of mean_df
		if len(t) < len(mean_df):
			t.extend([np.nan] * (len(mean_df) - len(t)))
		elif len(t) > len(mean_df):
			t = t[:len(mean_df)]
    
		# Add the adjusted 't' column to the DataFrame
		mean_df['t'] = t
		
		# Convert the final DataFrame to a dictionary
		result_dict = mean_df.to_dict(orient='list')
		
		return result_dict
	
	def stop_and_write(self):
		''' Stop logging data at the end of a sample and save the information.
		'''
		self.log = False
		data_lists = [self.sample_list, self.Fx_list, self.Fy_list, self.Fz_list]
		processed_data = self.avg_force(data_lists, self.t)
		
		try:
			# Save time-series force data, after finding the average force for each frame
			with open(os.path.join(self.timeseriesPath, f'sample_{self.i}.pkl'), 'wb') as handle:
				pickle.dump(processed_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
			
			# For single frame capture (i.e. if not intending to use data for time-series analysis):
			if self.time_series == False:
				time.sleep(0.1)
				filenames = os.listdir(self.videoframesPath)
				max_value = max(int(filename.strip('frame_.png')) for filename in filenames)
				i = 0
				while i < max_value:
					# Removes video frames apart from the last frame:
					os.remove(f'{self.videoframesPath}/frame_{i}.png')
					i=i+1
				i=0
		except:
			pass
		
		# Reset variables:
		self.t = []
		self.Fx_list = []
		self.Fy_list = []
		self.Fz_list = []
		self.sample_list = []
		self.sample = 0

	############################# FT SENSOR FUNCTIONS ##################################
	def _read_volts_once(self):
		"""从 NI-DAQ 读取 6 路电压（单帧）。"""
		v = self._ai_task.read()  # list 长度=6
		return [float(x) for x in v]

	def _bias_from_volts(self, volts6):
		"""调用 ATI DLL 的 Bias（以电压为基准置零）。"""
		import ctypes as C
		from ctypes import c_double
		v_arr = (c_double * 6)(*volts6)
		self._lib.atift_bias6(self._cal, v_arr)
		self._biased = True

	def tare(self, n = 200):
		"""归零：连续读取 n 帧电压均值 → Bias。"""
		import statistics
		buf = [self._read_volts_once() for _ in range(n)]
		means = [statistics.fmean(ch) for ch in zip(*buf)]
		self._bias_from_volts(means)
		self.mean = means[:]   # 兼容旧语义
		return means

	def zero(self):
		"""取消偏置（兼容旧接口）。"""
		self.mean = [0] * 6
		self._bias_from_volts([0,0,0,0,0,0])
		self._biased = False

	def receive(self):
		"""读取一帧：NI-DAQ 电压 → ATI DLL 转 Fx,Fy,Fz,Tx,Ty,Tz（N, N·m）。"""
		import ctypes as C
		from ctypes import c_double

		volts = self._read_volts_once()
		v_arr = (c_double * 6)(*volts)
		out  = (c_double * 6)()
		self._lib.atift_convert6(self._cal, v_arr, out)
		ft = [out[i] for i in range(6)]
		self.data = ft

		if self.log and self.cam_ready:
			Fx, Fy, Fz = ft[0], -1*ft[1], -1*ft[2]
			lock.acquire()
			try:
				self.Fx_list.append(float(Fx))
				self.Fy_list.append(float(Fy))
				self.Fz_list.append(float(Fz))
				self.sample_list.append(self.sample)
			finally:
				lock.release()
		return self.data

	def measurement(self):
		return getattr(self, 'data', [0]*6)

	def getMeasurement(self):
		self.receive()
		return self.data

	def getForce(self):
		return self.getMeasurement()[:3]

	def force(self):
		return self.measurement()[:3]

	def getTorque(self):
		return self.getMeasurement()[3:]

	def torque(self):
		return self.measurement()[3:]

	def receiveHandler(self):
		while self.stream:
			self.receive()

	def startStreaming(self, handler = True):
		if not self._biased:
			self.tare(n=200)   # 启动前自动归零（可按需保留/移除）
		if handler:
			self.stream = True
			self.thread = Thread(target = self.receiveHandler)
			self.thread.daemon = True
			self.thread.start()

	def stopStreaming(self):
		self.stream = False
		sleep(0.1)


	def image_worker(self):
		# Worker thread which captures image data while self.log = True
		while self.threadRun:
			if self.log:
				try:
					self.cam_ready = True
					self.t.append(time.time())
					success, self.frame = self.cam.read()
					self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
					
					if self.display_image:
						cv2.imshow("capture", self.frame) # Display video stream
					
					if self.resize[0]:
						self.frame = cv2.resize(self.frame, (self.resize[1]))
					cv2.imwrite(os.path.join(self.videoframesPath, f'frame_{self.sample}.png'), self.frame)
					
					cv2.waitKey(1)

					if success == False:
						print('No image data')
						break
					self.sample = self.sample +1

				except Exception as e:
					print(f'Error in image worker thread: {e}')
					break
		self.stop()

	def returnData(self):
		return [self.t, self.Fx_list, self.Fy_list, self.Fz_list]
			
	def stop(self):
		if self.threadRun:
			self.threadRun = False

			self.imageThread.join()
			self.stopStreaming()
			print("Main threads joined successfully")

	def close(self):
		self.stop()

lock = Lock()
