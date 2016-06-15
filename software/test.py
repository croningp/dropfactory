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

#
from manager import manager
from tools.xp_watcher import XPWatcher

from tools.xp_maker import add_XP_to_pool_folder

oil_ratios = {
    'octanol': 21,
    'octanoic': 14,
    'pentanol': 19,
    'dep': 46
    }

pool_folder = os.path.join(HERE_PATH, 'test_pool_folder')

for _ in range(4):
    add_XP_to_pool_folder(oil_ratios, pool_folder)

watcher = XPWatcher(manager, pool_folder)
