import os
import time
import json
import threading

import filetools

SLEEP_TIME = 1

XP_PARAMS_FILENAME = 'params.json'
VIDEO_FILENAME = 'video.avi'


def read_XP_from_file(filename):
    with open(filename) as f:
        return json.load(f)


class XPWatcher(threading.Thread):

    def __init__(self, manager, folder_to_watch, param_filename=XP_PARAMS_FILENAME, ignore_filename=VIDEO_FILENAME, verbose=True):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.manager = manager
        self.folder_to_watch = folder_to_watch
        self.param_filename = param_filename
        self.ignore_filename = ignore_filename

        self.processed_folder = []

        self.verbose = verbose

        self.start()

    def run(self):
        self.interrupted.acquire()
        while self.interrupted.locked():
            folders = filetools.list_folders(self.folder_to_watch)
            folders.sort()
            for folder in folders:
                if folder not in self.processed_folder:
                    param_file = os.path.join(folder, self.param_filename)
                    ignore_file = os.path.join(folder, self.ignore_filename)
                    if os.path.exists(param_file) and not os.path.exists(ignore_file):
                        if self.verbose:
                            print 'Adding {} to manager queue'.format(param_file)
                        XP_dict = read_XP_from_file(param_file)
                        self.manager.add_XP(XP_dict)
                        self.processed_folder.append(folder)
            time.sleep(SLEEP_TIME)

    def stop(self):
        self.interrupted.release()
