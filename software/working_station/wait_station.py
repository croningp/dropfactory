import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

import time

from tools.tasks import Task


class WaitStation(Task):

    def __init__(self):
        Task.__init__(self)
        self.start()

    def main(self):
        if 'min_waiting_time' in self.XP_dict:
            time.sleep(self.XP_dict['min_waiting_time'])
