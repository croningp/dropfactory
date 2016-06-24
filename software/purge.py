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

XP_list = []

XP_list.append({
    'min_waiting_time': 60,
    'surfactant_volume': 1,
    'formulation': {
        'octanol': 1,
        'octanoic': 0,
        'pentanol': 0,
        'dep': 0
    }
})

XP_list.append({
    'min_waiting_time': 60,
    'surfactant_volume': 1,
    'formulation': {
        'octanol': 0,
        'octanoic': 0,
        'pentanol': 1,
        'dep': 0
    }
})

XP_list.append({
    'min_waiting_time': 60,
    'surfactant_volume': 1,
    'formulation': {
        'octanol': 0,
        'octanoic': 1,
        'pentanol': 0,
        'dep': 0
    }
})

XP_list.append({
    'min_waiting_time': 60,
    'surfactant_volume': 1,
    'formulation': {
        'octanol': 0,
        'octanoic': 0,
        'pentanol': 0,
        'dep': 1
    }
})

start_time = time.time()

# we do 4 times each
for _ in range(4):
    for XP_dict in XP_list:
        manager.add_XP(XP_dict)

manager.wait_until_XP_finished()

elapsed = time.time() - start_time

print 'Purge took {} seconds'.format(elapsed)
