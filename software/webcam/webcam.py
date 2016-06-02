import os
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)



from chemobot_tools.v4l2 import V4L2
from chemobot_tools.video_recorder import VideoRecorder

# setting up the device
configfile = os.path.join(HERE_PATH, 'webcam_config.json')
vidconf = V4L2.from_configfile(configfile)

# creating the video_recorder instance
import json
device = None
with open(configfile) as f:
    device = json.load(f)['device']
video_recorder = VideoRecorder(device)


if __name__ == '__main__':
    video_recorder.record_to_file('video.avi', duration_in_sec=10)
    video_recorder.wait_until_idle()
