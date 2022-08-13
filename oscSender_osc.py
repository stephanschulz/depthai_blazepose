import cv2
import numpy as np

from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
OSC_ADDRESS = "/depthai_pose"

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
                showVideo=None):
        self.sender = sender
        self.frame = None
        self.pause = False

        # Rendering flags
        self.show_rot_rect = False
        self.show_landmarks = True
        self.show_score = False
        self.show_fps = True

        self.show_xyz_zone = self.show_xyz = self.sender.xyz

        # create osc client
        # client = udp_client.SimpleUDPClient(args.ip, args.port, True)
        self.client = udp_client.SimpleUDPClient("10.100.0.101", 12345, True)
        
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
                
        
    def draw(self, frame, body):
        if not self.pause:
            self.frame = frame
            if body:
                self.draw_landmarks(body)
            self.body = body
        elif self.frame is None:
            self.frame = frame
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
            client.send_message(OSC_ADDRESS, 0)
            return

# https://github.com/attwad/python-osc/blob/master/pythonosc/osc_message_builder.py
        # create message and send
        builder = OscMessageBuilder(address=OSC_ADDRESS)
        theFPS = round(self.sender.fps.get_global(),2)
#        print("fps:",theFPS)
#        print("len(body.landmarks):",len(body.landmarks))
        builder.add_arg(theFPS, arg_type='f')
        builder.add_arg(len(body.landmarks), arg_type='i')
        builder.add_arg(1)
                    
        for i,oneLM in enumerate(body.landmarks):
            if self.is_present(body, i):
#                print ("lm",i, "x", oneLM[0], "y", oneLM[1], "z", oneLM[2])
                builder.add_arg(i, arg_type='i')
                builder.add_arg(oneLM[0], arg_type='i')
                builder.add_arg(oneLM[1], arg_type='i')
                builder.add_arg(oneLM[2], arg_type='i')
                # visibility
                # builder.add_arg(x_y_z_v[3])
                
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
        
            
