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
from robot import robot

from working_station.fill_petri_dish import FillPetriDish
from working_station.clean_petri_dish import CleanPetriDish

import time


XP = {
'surfactant_volume': 3.5
}

pump.controller.smart_initialize()

a = FillPetriDish(pump.controller.surfactant)
a.launch(XP)

b= CleanPetriDish(robot.CLEAN_HEAD_DISH,
                  pump.controller.waste_dish, pump.controller.water_dish, pump.controller.acetone_dish)
b.launch(XP)

start = time.time()

print 'toto'


a.wait_until_idle()
b.wait_until_idle()

print time.time() - start
