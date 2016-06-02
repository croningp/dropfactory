import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

from tools.tasks import Task
from webcam import webcam


class RecordVideo(Task):

    def __init__(self):
        Task.__init__(self)
        self.start()

    def main(self):
        video_info = self.XP_dict['video_info']

        webcam.video_recorder.record_to_file(video_info['path'], duration_in_sec=video_info['duration'])
        webcam.video_recorder.wait_until_idle()
