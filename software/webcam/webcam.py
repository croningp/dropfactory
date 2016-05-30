from chemobot_tools.v4l2 import V4L2
from chemobot_tools.video_recorder import VideoRecorder

DEVICE = 1

# setting up the device
vidconf = V4L2(DEVICE)
vidconf.apply_config_from_file('./webcam_config.json')


# creating the video_recorder instance
video_recorder = VideoRecorder(DEVICE)



if __name__ == '__main__':
    video_recorder.record_to_file('video.avi', duration_in_sec=10)
    video_recorder.wait_until_idle()
