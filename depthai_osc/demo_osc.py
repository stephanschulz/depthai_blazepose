#!/usr/bin/env python3

#https://github.com/geaxgx/depthai_blazepose

#from BlazeposeRenderer_osc import BlazeposeRenderer
from oscSender_osc import oscSender

#Python3.8 demo_osc.py -e -v --oscIP "10.100.0.101" --oscPort 12345 --xyz

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-e', '--edge', action="store_true",
                    help="Use Edge mode (postprocessing runs on the device)")
parser_tracker = parser.add_argument_group("Tracker arguments")                 
parser_tracker.add_argument('-i', '--input', type=str, default="rgb", 
                    help="'rgb' or 'rgb_laconic' or path to video/image file to use as input (default=%(default)s)")
parser_tracker.add_argument("--pd_m", type=str,
                    help="Path to an .blob file for pose detection model")
parser_tracker.add_argument("--lm_m", type=str,
                    help="Landmark model ('full' or 'lite' or 'heavy') or path to an .blob file")
parser_tracker.add_argument('-xyz', '--xyz', action="store_true", 
                    help="Get (x,y,z) coords of reference body keypoint in camera coord system (only for compatible devices)")
parser_tracker.add_argument('-c', '--crop', action="store_true", 
                    help="Center crop frames to a square shape before feeding pose detection model")
parser_tracker.add_argument('--no_smoothing', action="store_true", 
                    help="Disable smoothing filter")
parser_tracker.add_argument('-f', '--internal_fps', type=int, 
                    help="Fps of internal color camera. Too high value lower NN fps (default= depends on the model)")                    
parser_tracker.add_argument('--internal_frame_height', type=int, default=450,                                                                                    
                    help="Internal color camera frame height in pixels (default=%(default)i)")                    
parser_tracker.add_argument('-s', '--stats', action="store_true", 
                    help="Print some statistics at exit")
parser_tracker.add_argument('-t', '--trace', action="store_true", 
                    help="Print some debug messages")
parser_tracker.add_argument('--force_detection', action="store_true", 
                    help="Force person detection on every frame (never use landmarks from previous frame to determine ROI)")

parser_tracker.add_argument('-v', '--showVideo', action="store_true",
                    help="Display skeleton in 3d in a separate window. See README for description.")   

#parser_renderer = parser.add_argument_group("Renderer arguments")
#parser_renderer.add_argument('-3', '--show_3d', choices=[None, "image", "world", "mixed"], default=None,
#                    help="Display skeleton in 3d in a separate window. See README for description.")
#parser_renderer.add_argument("-o","--output",
#                    help="Path to output video file")
 
parser_osc = parser.add_argument_group("OSC arguments")    
parser_osc.add_argument('--oscIP', type=str, help="osc ip to send data to")     
parser_osc.add_argument('--oscPort', type=int, help="osc port to send data to")    
            
args = parser.parse_args()

if args.edge:
    from BlazeposeDepthaiEdge_osc import BlazeposeDepthai
else:
    from BlazeposeDepthai import BlazeposeDepthai
tracker = BlazeposeDepthai(input_src=args.input, 
            pd_model=args.pd_m,
            lm_model=args.lm_m,
            smoothing=not args.no_smoothing,   
            xyz=args.xyz,            
            crop=args.crop,
            internal_fps=args.internal_fps,
            internal_frame_height=args.internal_frame_height,
            force_detection=args.force_detection,
            stats=True,
            trace=args.trace)   

osc_sending = oscSender(tracker,
                        oscIP = args.oscIP,
                        oscPort = args.oscPort)

#renderer = BlazeposeRenderer(
#                tracker, 
#                show_3d=args.show_3d, 
#                output=args.output)

while True:
    # Run blazepose on next frame
    rgb_frame, right_frame, body = tracker.next_frame()
    if rgb_frame is None: break
    # Draw 3d skeleton
    osc_sending.update(body)
    #print("args.showVideo",args.showVideo)
#    if args.showVideo is True:
    if args.showVideo:
       
        frame = osc_sending.draw(rgb_frame, right_frame, body)
        # frame = renderer.draw(frame, body)
        # key = renderer.waitKey(delay=1)
        key = osc_sending.waitKey(delay=1)
        if key == 27 or key == ord('q'):
            break
    else:
        print("args.showVideo",args.showVideo)
        
#osc_sending.exit()
#renderer.exit()
tracker.exit()
