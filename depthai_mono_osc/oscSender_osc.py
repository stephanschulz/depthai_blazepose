#https://github.com/cansik/mediapipe-osc/blob/main/pose.py

import cv2
import numpy as np
import json

from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
OSC_ADDRESS = "/depthai_pose"
OSC_ADDRESS_NOBODY = "/depthai_pose_info"

# LINE_BODY and COLORS_BODY are used when drawing the skeleton in 3D. 
rgb = {"right":(0,1,0), "left":(1,0,0), "middle":(1,1,0)}
LINES_BODY = [[9,10],[4,6],[1,3],
            [12,14],[14,16],[16,20],[20,18],[18,16],
            [12,11],[11,23],[23,24],[24,12],
            [11,13],[13,15],[15,19],[19,17],[17,15],
            [24,26],[26,28],[32,30],
            [23,25],[25,27],[29,31]]

COLORS_BODY = ["middle","right","left",
                "right","right","right","right","right",
                "middle","middle","middle","middle",
                "left","left","left","left","left",
                "right","right","right","left","left","left"]
COLORS_BODY = [rgb[x] for x in COLORS_BODY]

class oscSender:
    def __init__(self,
                sender,
                oscIP = "127.0.0.1",
                oscPort = 12345):
                
        self.sender = sender
        self.frame = None
        self.pause = False

        self.oscIP = oscIP
        self.oscPort = oscPort
        
        # Rendering flags
        self.show_rot_rect = False
        self.show_landmarks = True
        self.show_score = False
        self.show_fps = True

        self.show_xyz_zone = self.show_xyz = self.sender.xyz

        # create osc client
        # client = udp_client.SimpleUDPClient(args.ip, args.port, True)
#        self.client = udp_client.SimpleUDPClient("10.100.0.101", 12345, True)
        self.client = udp_client.SimpleUDPClient(self.oscIP, self.oscPort, True)
        
    def is_present(self, body, lm_id):
        return body.presence[lm_id] > self.sender.presence_threshold

    def draw_landmarks(self, body):
        if self.show_rot_rect:
            cv2.polylines(self.frame, [np.array(body.rect_points)], True, (0,255,255), 2, cv2.LINE_AA)
        if self.show_landmarks:                
            list_connections = LINES_BODY
            lines = [np.array([body.landmarks[point,:2] for point in line]) for line in list_connections if self.is_present(body, line[0]) and self.is_present(body, line[1])]
            cv2.polylines(self.frame, lines, False, (255, 180, 90), 2, cv2.LINE_AA)
            
            # for i,x_y in enumerate(body.landmarks_padded[:,:2]):
            for i,x_y in enumerate(body.landmarks[:self.sender.nb_kps,:2]):
                if self.is_present(body, i):
                    if i > 10:
                        color = (0,255,0) if i%2==0 else (0,0,255)
                    elif i == 0:
                        color = (0,255,255)
                    elif i in [4,5,6,8,10]:
                        color = (0,255,0)
                    else:
                        color = (0,0,255)
                    cv2.circle(self.frame, (x_y[0], x_y[1]), 4, color, -11)
        if self.show_score:
            h, w = self.frame.shape[:2]
            cv2.putText(self.frame, f"Landmark score: {body.lm_score:.2f}", 
                        (20, h-60), 
                        cv2.FONT_HERSHEY_PLAIN, 2, (255,255,0), 2)
                
        
    def draw(self, mono_manip, body):
        if not self.pause:
            self.frame = mono_manip
#            s_img = cv2.resize(mono_manip, (0,0), fx=0.4, fy=0.4) 
#            s_img = cv2.cvtColor(s_img,cv2.COLOR_GRAY2RGB)
#            x_offset=rgb_frame.shape[1]-s_img.shape[1]
#            y_offset=0
#            self.frame[y_offset:y_offset+s_img.shape[0], x_offset:x_offset+s_img.shape[1]] = s_img
            if body:
                self.draw_landmarks(body)
            self.body = body
        elif self.frame is None:
            self.frame = mono_manip
            self.body = None
        # else: self.frame points to previous frame
        
        # send the pose over osc
#        self.send_pose(self.client, body)

        return self.frame
    
    def update(self, body):
        # send the pose over osc
        self.send_pose(self.client, body)
        
    def send_pose(self, client: udp_client, body):
              
        if body is None:
            client.send_message(OSC_ADDRESS_NOBODY, 0)
            return

# https://github.com/attwad/python-osc/blob/master/pythonosc/osc_message_builder.py
        # create message and send
        builder = OscMessageBuilder(address=OSC_ADDRESS)
        theFPS = round(self.sender.fps.get_global(),2)
#        print("fps:",theFPS)
#        print("len(body.landmarks):",len(body.landmarks))
#        builder.add_arg(theFPS, arg_type='f')
#        builder.add_arg(len(body.landmarks), arg_type='i')
#        builder.add_arg(1)
               
#               send tracking data as long string over OSC     
#        for i,oneLM in enumerate(body.landmarks):
#            if self.is_present(body, i):
##                print ("lm",i, "x", oneLM[0], "y", oneLM[1], "z", oneLM[2])
#                builder.add_arg(i, arg_type='i')
#                builder.add_arg(body.visibility[i], arg_type='i')
#                builder.add_arg(oneLM[0], arg_type='i')
#                builder.add_arg(oneLM[1], arg_type='i')
#                builder.add_arg(oneLM[2], arg_type='i')
#                # visibility
#                # builder.add_arg(x_y_z_v[3])
#                
#        msg = builder.build()
#        client.send(msg)
    
#    send tracking data as json object over OSC
#        print("body.presence ",body.presence)
#        print("body.visibility ",body.visibility)
        print("body.xyz ",body.xyz)
        if body.presence[0] > 0.4:
            data=[]
            for i,oneLM in enumerate(body.landmarks):
                if self.is_present(body, i):
                    item = {"visibility": round(float(body.visibility[i]),4)}
                    item["x"] = round(float((oneLM[0] - body.xyz[0]) * 0.001),4); #left right
                    item["y"] = round(float((oneLM[1] - body.xyz[1]) * 0.001),4); #up down
                    item["z"] = round(float((oneLM[2] - body.xyz[2]) * 0.001),4); #front back
#                    item["x"] = round(float(oneLM[0] * 0.001),4);
#                    item["y"] = round(float(oneLM[1] * 0.001),4);
#                    item["z"] = round(float(oneLM[2] * 0.001),4);
#                    print("item",item)
                    data.append(item)
#            print("len data ",len(data))
#        if data:
    #        print("data",data)
            jsonData=json.dumps(data)
    #        print("jsonData",jsonData)
            builder.add_arg(int(len(data)), arg_type='i')
            builder.add_arg(jsonData, arg_type='s')
            msg = builder.build()
            client.send(msg)
        
#    def exit(self):
#        if self.output:
#            self.output.release()

    def waitKey(self, delay=1):
        if self.show_fps:
            self.sender.fps.draw(self.frame, orig=(50,50), size=1, color=(240,180,100))
        cv2.imshow("Blazepose", self.frame)
#        if self.output:
#            self.output.write(self.frame)
        key = cv2.waitKey(delay) 
        if key == 32:
            # Pause on space bar
            self.pause = not self.pause
        elif key == ord('r'):
            self.show_rot_rect = not self.show_rot_rect
        elif key == ord('l'):
            self.show_landmarks = not self.show_landmarks
        elif key == ord('s'):
            self.show_score = not self.show_score
        elif key == ord('f'):
            self.show_fps = not self.show_fps
        elif key == ord('x'):
            if self.sender.xyz:
                self.show_xyz = not self.show_xyz    
        elif key == ord('z'):
            if self.sender.xyz:
                self.show_xyz_zone = not self.show_xyz_zone 
        return key
        
            
