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
from working_station.clean_petri_dish import CleanPetriDish
from working_station.clean_oil_parts import CleanOilParts

from constants import N_POSITION

XP = {
    'surfactant_volume': 3.5,
    'formulation': {
        'octanol': 1,
        'octanoic': 1,
        'pentanol': 0,
        'dep': 0.1
    }
}


clean_dish_station = CleanPetriDish(robot.CLEAN_HEAD_DISH,
                                    robot.CLEAN_HEAD_DISH_SWITCH,
                                    pump.controller.waste_dish,
                                    pump.controller.water_dish,
                                    pump.controller.acetone_dish)

clean_oil_station = CleanOilParts(robot.XY,
                                   robot.Z,
                                   robot.SYRINGE,
                                   robot.CLEAN_HEAD_MIXTURE,
                                   pump.controller.waste_oil,
                                   pump.controller.acetone_oil)

import time

start_time_total = time.time()
for i in range(N_POSITION):
    start_time = time.time()
    print '###\nCleaning {}/{}'.format(i + 1, N_POSITION)

    # start cleaning
    clean_dish_station.launch(XP)
    clean_oil_station.launch(XP, clean_tube=True, clean_syringe=False)

    # wait till finished
    clean_dish_station.wait_until_idle()
    clean_oil_station.wait_until_idle()

    # rotate
    robot.rotate_geneva_wheels()

    elapsed = time.time() - start_time
    print 'It took {} seconds'.format(elapsed)

elapsed_total = time.time() - start_time_total
print '###\nThe all cleaning cycle took {} seconds'.format(elapsed_total)
