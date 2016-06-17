import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
sys.path.append(HERE_PATH)

import logging
logging.basicConfig(level=logging.INFO)

import time

##
from manager import manager

XP_dict = {
    'force_clean_syringe': True
}

start_time = time.time()

manager.add_XP(XP_dict)
manager.wait_until_XP_finished()

elapsed = time.time() - start_time

print 'Clean syringe took {} seconds'.format(elapsed)
