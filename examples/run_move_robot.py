from cri.robot import SyncRobot, AsyncRobot
from cri.controller import RTDEController
import time
from ipdb import set_trace
import math

tcp = 65
offset = -3

base_frame = (0, 0, 0, 0, 0, 0)  
# base frame: x->front, y->right, z->up (higher z to make sure doesnt press into the table)
#57.5
#work_frame = (473, -111, 61-offset, -180, 0, -90)            # For 0 degrees, #change the Z bigger to be safe
work_frame = (498, -111, 43, -180, 0, -90)  #for mini45
#work_frame = (473, -40, 65-offset, -180, 0, -90)           # safe baseframe for testing, using a box
tcp_x_offset = -1.2    #bigger, tip forward deeper
tcp_y_offset = 0.9#1.25   #y bigger, tip right deeper 

with AsyncRobot(SyncRobot(RTDEController(ip='192.11.72.20'))) as robot:
    time.sleep(1)


    tcp_x = tcp_x_offset*math.sin(math.pi/4) + tcp_y_offset*math.cos(math.pi/4)
    tcp_y = tcp_x_offset*math.cos(math.pi/4) - tcp_y_offset*math.sin(math.pi/4)

    robot.tcp = (tcp_x, tcp_y, tcp+ offset-0.25 , 0, 0, -45) # 60 if tcp at the center of the hemisphere, otherwise 75 is keeping the tcp on the skin
    # 85mm is true tcp but when rotating at large angles, it might crush the sensor
    robot.axes = "sxyz"
    robot.linear_speed = 30
    robot.angular_speed = 30
    robot.coord_frame = work_frame
    set_trace()
    robot.move_linear((0, 0, 0, 0, 0, 0)) #move to home position
    print('Moved to home position')
    set_trace()

    # # Test ranges
    try:
        while True:
            robot.linear_speed = 30
            robot.move_linear((0, 0, 0., -0, 0, 0))
            time.sleep(1)
            robot.move_linear((0, 0, 0 ,-34,0, 0))
            time.sleep(1)
            robot.move_linear((0, 0, 0., -0, 0, 0))
            time.sleep(1)
            robot.move_linear((0, 0, 0., 34,0, 0)) 
            time.sleep(1)
            # robot.move_linear((0, 0, 0., -0, 34, 0))
            # time.sleep(1)
            # robot.move_linear((0, 0, 0., -0, 0, 0))
            # time.sleep(1) 
            # robot.move_linear((0, 0, 0., -0, -34, 0))
            # time.sleep(1)

            # robot.move_linear((0, 0, 0.5, 34, 0, 0)) # Moved to x rotation lower
            # robot.move_linear((0, 0, 0.5, -34, 0, 0))

            # robot.move_linear((0, 0, 1, 0, 34, 0)) # Moved to x rotation higher

            # robot.move_linear((0, 0, 1, 0, -34, 0))

            set_trace()
    except:
        print("quit")

    # try:
    #     while True: 
    #         robot.linear_speed = 30
    #         robot.move_linear((0, 0, 0, 0, -35, 0)) # Moved to y rotation lower
    #         robot.move_linear((0, 0, 0, 0, 0, 0))
    #         robot.move_linear((0, 0, 0, 0, 35, 0)) # Moved to y rotation higher
    #         robot.move_linear((0, 0, 0, 0, 0, 0))
    #         set_trace()
    # except:
    #     print('Moving to safe location')
    
    robot.linear_speed = 50
    robot.move_linear((0, 0, -50, 0, 0, 0)) #move to a bit higher position to avoid damaging the sensor