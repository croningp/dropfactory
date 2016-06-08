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
from pump import pump
if not pump.controller.are_pumps_initialized():
    raise Exception('Pumps not initalized, run initialize.py script first')

from robot import robot
robot.init()

##
from working_station.clean_oil_parts import CleanSyringe

from constants import N_POSITION

XP_dict = {}


from working_station.clean_oil_parts import CleanOilParts
clean_oil_station = CleanOilParts(robot.XY,
                                  robot.Z,
                                  robot.SYRINGE,
                                  robot.CLEAN_HEAD_MIXTURE,
                                  pump.controller.waste_oil,
                                  pump.controller.acetone_oil)


import time

start_time_total = time.time()

clean_oil_station.launch(XP_dict, clean_tube=False, clean_syringe=True)
clean_oil_station.wait_until_idle()

elapsed_total = time.time() - start_time_total
print '###\nCleaning the syringe took {} seconds'.format(elapsed_total)
