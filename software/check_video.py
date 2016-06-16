import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
sys.path.append(HERE_PATH)

import logging
logging.basicConfig(level=logging.INFO)

##
from working_station.record_video import RecordVideo

XP_dict = {
    'video_info': {
        'filename': os.path.join(HERE_PATH, 'video.avi'),
        'duration': 10
    }
}

record_video_station = RecordVideo()
record_video_station.launch(XP_dict)
record_video_station.wait_until_idle()
