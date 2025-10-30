import os
import pandas as pd
import numpy as np
import math
import shutil
import time
import random

from gather_data import DataGatherer
from gather_data_mini45 import DataGatherer_45

from cri.robot import SyncRobot, AsyncRobot
from cri.controller import RTDEController

from tactile_feature_extraction import TIP_ID
from tactile_feature_extraction import ROOT_PATH
from tactile_feature_extraction import BASE_DATA_PATH

def make_target_df(target_df_file, poses_rng, num_poses, num_frames=1, obj_poses=[[0,]*6], moves_rng=[[0,]*6,]*2, **kwargs):
    np.random.seed(0)  # 设定随机种子，确保可复现

    # 生成随机的位姿 (pose) 和运动量 (move)
    poses = np.random.uniform(low=poses_rng[0], high=poses_rng[1], size=(num_poses, 6))
    poses = poses[np.lexsort((poses[:,1], poses[:,5]))]  # 按 yaw 和 y 轴排序
    moves = np.random.uniform(low=moves_rng[0], high=moves_rng[1], size=(num_poses, 6))

    # 定义 DataFrame 列名
    pose_ = [f"pose_{_+1}" for _ in range(6)]
    move_ = [f"move_{_+1}" for _ in range(6)]
    target_df = pd.DataFrame(columns=["image_name", "data_name", "obj_id", "pose_id", *pose_, *move_])

    for i in range(num_poses * len(obj_poses)):  # 遍历所有物体的位姿组合
        data_name = f"frame_{i}"
        i_pose, i_obj = (int(i % num_poses), int(i / num_poses))  # 计算索引

        # 95% 概率正常使用随机生成的位姿和运动量，5% 概率使用全 0
        if np.random.random() < 0.05:  # 5% 的概率
            pose = [0,0,0,0,0,0]  # 全 0 的位姿
            move = np.zeros(6)  # 全 0 的运动量
        else:
            pose = poses[i_pose, :] + obj_poses[i_obj]  # 计算实际位姿
            move = moves[i_pose, :]  # 取出对应的运动量

        for f in range(num_frames):  # 处理多个帧
            frame_name = f"frame_{i}_{f}.png"
            # 添加到 DataFrame
            target_df.loc[len(target_df)] = np.hstack((frame_name, data_name, i_obj+1, i_pose+1, pose, move))

    # 保存到 CSV
    target_df.to_csv(target_df_file, index=False)
    return target_df

def collect(target_df, dataPath, resume_from, sleep_time, i):
    
    # collect one data and flush the sample
    flush = False
    for _, row in target_df.iloc[resume_from:].iterrows():
        if not flush:
            # Take first sample and disregard to clear buffer:
            pose = row.loc['pose_1' : 'pose_6'].values.astype(float)
            move = row.loc['move_1' : 'move_6'].values.astype(float)
            print(f'pose for frame_{i} = {pose}')
            # Add extra depth to account additional geomrtry in Rx direction, adding more depth from 0 deg to 22 deg
            add_tap_depth = max((34 - abs(pose[3]))/34 * 2., 0.0)
            add_tap_depth = 0

            # check if pose is zero, raise tip more to avoid contact
            if not any(pose):
                add_tap_depth-= 2
            add_tap = [0,0,add_tap_depth,0,0,0]
            # print('Tap deep', add_tap_depth)
            tap = [0,0,pose[2] ,0,0,0]
            pose = (pose - tap)
            robot.move_linear(pose - move)
            dg.begin_sample(i)
            robot.move_linear(pose - move + tap + add_tap)
            robot.linear_speed = 10
            time.sleep(0.25)
            robot.move_linear(pose + tap + add_tap)

            time.sleep(sleep_time)
            dg.stop_and_write()
            robot.linear_speed = 200
            robot.move_linear((0, 0, -10, 0, 0, 0))
            time.sleep(sleep_time)
            os.remove(f'{dataPath}/time_series/sample_{i}.pkl')
            shutil.rmtree(f'{dataPath}/videos/sample_{i}')
            flush = True
        else:
            print('flushed - moving on to main samples')
            break
    
    # Main data collection
    for _, row in target_df.iloc[resume_from:].iterrows():
        try:
            if dg.threadRun == False:
                print('DataGatherer stopped streaming, exiting...')
                break
            # Get pose:
            i_obj, i_pose = (int(row.loc["obj_id"]), int(row.loc["pose_id"]))
            pose = row.loc['pose_1' : 'pose_6'].values.astype(float)
            move = row.loc['move_1' : 'move_6'].values.astype(float)
            print(f'pose for frame_{i} = {pose}')
            # Add extra depth to account additional geomrtry in Rx direction, adding more depth from 0 deg to 22 deg
            add_tap_depth = max((34 - abs(pose[3]))/34 * 2., 0.0)
            # check if pose is zero, raise tip more to avoid contact
            if not any(pose):
                add_tap_depth-= 2
            #add_tap_depth=0
            add_tap = [0,0,add_tap_depth,0,0,0]
            # print('Tap deep', add_tap_depth)
            tap = [0,0,pose[2] ,0,0,0]
            pose = (pose - tap)
            robot.move_linear(pose - move)
            dg.begin_sample(i)
            robot.move_linear(pose - move + tap + add_tap)
            robot.linear_speed = 10
            time.sleep(0.25)
            robot.move_linear(pose + tap + add_tap)
            time.sleep(sleep_time)
            dg.stop_and_write()
            robot.linear_speed = 200
            robot.move_linear((0, 0, -10, 0, 0, 0))

            # time.sleep(sleep_time)

            # sample_size = os.path.getsize(f'{dataPath}/time_series/sample_{i}.pkl') #check FT sensor is still working

            # if sample_size < 55000:
            #     dg.pause()
            #     os.remove(f'{dataPath}/time_series/sample_{i}.pkl')
            #     shutil.rmtree(f'{dataPath}/videos/sample_{i}')
            #     print(f'sample {i} under threshold at {sample_size}, removed and exiting...')
            #     break

            i = i+1   
        except:
            print(f'something went wrong sample_{i} - moving on...')
            break

tcp = 65    # DONT CHANGE THIS VALUE, CHANgE "offset" INSTEAD!!!!
offset = -3
base_frame = (0, 0, 0, 0, 0, 0)  
# base frame: x->front, y->bigger2right, z->bigger2up (higher z to make sure doesnt press into the table)
#work_frame = (473, -40, 65-offset, -180, 0, -90) #safe pose
work_frame = (498, -111, 41.3, -180, 0, -90) #y-111   z#low the height lower, Bigger Z would be safer
tcp_x_offset = -1.2    # Change this value to adjust the tcp in the forward backward direction, negative value moves tcp away the robot
tcp_y_offset = 0.9     # Change this value to adjust the tcp in the left right direction, negative value moves tcp to the right


tcp_x = tcp_x_offset*math.sin(math.pi/4) + tcp_y_offset*math.cos(math.pi/4)
tcp_y = tcp_x_offset*math.cos(math.pi/4) - tcp_y_offset*math.sin(math.pi/4)
#change theq cam from data_collection/gather_data
# Resume from last completed sample +1 (0 for new dataset):
resume_from = 1625

if resume_from == 0:
    resume = False
    poses_rng = [[0, 0, 0.5,-34,-34,0], [0, 0, 4,34,34, 0]]    # pose ranges (min values, max values)
    #poses_rng = [[0, 0,0.5,0, -34, 0], [0, 0, 0.5,0,-34, 0]]    # pose ranges (min values, max values)

    num_poses = 3000
    num_frames = 1
    #moves_rng = [[0,0, 0, 0, 0, 0], [0,0, 0, 0, 0, 0]]    # Shear movements (min values, max values)
    moves_rng = [[2, 2, 0, 0, 0, 0], [-2,-2, 0, 0, 0, 0]]    # Shear movements (min values, max values)

    
    # Make data path
    folder = f"collect_{TIP_ID}_5D_surface" 
    dataPath = os.path.join(ROOT_PATH, folder)
    os.makedirs(dataPath, exist_ok=True)

    target_df = make_target_df(f"{dataPath}/targets.csv", poses_rng, num_poses, num_frames, obj_poses=[[0,]*6], moves_rng=moves_rng)
else:
    resume = True
    dataPath = BASE_DATA_PATH
    target_df = pd.read_csv(f'{dataPath}/targets.csv')

#with DataGatherer(resume=resume, dataPath=dataPath, time_series=False, display_image=True, FT_ip='192.168.1.1', resize=[False, (300,225)]) as dg, AsyncRobot(SyncRobot(RTDEController(ip='192.11.72.20'))) as robot:
with DataGatherer_45(resume=resume, dataPath=dataPath, time_series=False, display_image=True, resize=[False, (300,225)]) as dg, AsyncRobot(SyncRobot(RTDEController(ip='192.11.72.20'))) as robot:
    #dg = DataGatherer_45(resume=resume, dataPath=dataPath, time_series=False, display_image=True, resize=[False, (300,225)])
    #dg = DataGatherer(resume=resume, dataPath=dataPath, time_series=False, display_image=True, FT_ip='192.168.1.1', resize=[False, (300,225)]) 

    time.sleep(1)

    #robot movement#############################################################################
    # Setup robot (TCP, linear speed,  angular speed and coordinate frame):
    robot.tcp = (tcp_x, tcp_y, tcp + offset-0.25, 0, 0, -45) 
    robot.axes = "sxyz"
    robot.linear_speed = 50
    robot.angular_speed = 50
    robot.coord_frame = work_frame
    sleep_time = 0.5
    angle = 0
    i = resume_from
    flush = False
    robot.move_linear((0, 0, 0, 0, 0, 0)) #move to home position
    print('Moved to home position')
    #robot movement#############################################################################
    # Main data collection
    time.sleep(3)
    dg.start()
    time.sleep(2)
    collect(target_df, dataPath, resume_from, sleep_time, i)
    dg.stop()

    robot.linear_speed = 30
    robot.move_linear((0, 0, -50, 0, 0, 0)) #move to a bit higher position to avoid damaging the sensor