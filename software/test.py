import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
sys.path.append(HERE_PATH)

import logging
logging.basicConfig(level=logging.INFO)

#
from manager import manager
from tools.xp_watcher import XPWatcher

from tools.xp_maker import add_XP_to_pool_folder

# movement
oil_ratios = {
    "dep": 0.92019434642566544,
    "octanol": 0.7492601802279919,
    "octanoic": 0.0,
    "pentanol": 0.84013885086802531
}


#sink
# oil_ratios_2 = {
#     "dep": 1.0,
#     "octanol": 0.0,
#     "octanoic": 0.0,
#     "pentanol": 0.0
# }

# wobble
# oil_ratios_3 =  {
#     "dep": 0.0,
#     "octanol": 0.57284714859204744,
#     "octanoic": 0.91965021960068283,
#     "pentanol": 0.56743951850035534
# }


pool_folder = os.path.join(HERE_PATH, 'test_pool_folder')

for _ in range(15):
    add_XP_to_pool_folder(oil_ratios, pool_folder)
    # add_XP_to_pool_folder(oil_ratios_2, pool_folder)
    # add_XP_to_pool_folder(oil_ratios_3, pool_folder)

watcher = XPWatcher(manager, pool_folder)

# manager.wait_until_XP_finished()
