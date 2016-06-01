import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
sys.path.append(HERE_PATH)

import logging
logging.basicConfig(level=logging.INFO)

# home robot
raw_input('\n### Robot homing:\nMake sure the syringe and xyz system can go home safely, then press enter')
from robot import robot
robot.home()

# pump init
raw_input('\n### Pump initialization:\nmove the filling station on the side for pump initialization, then press enter')
from pump import pump
from constants import CLEAN_HEAD_DISH_UP
from constants import CLEAN_HEAD_DISH_DOWN
from constants import CLEAN_HEAD_MIXTURE_DOWN

robot.CLEAN_HEAD_DISH.set_angle(CLEAN_HEAD_DISH_DOWN)
robot.CLEAN_HEAD_MIXTURE.move_to(CLEAN_HEAD_MIXTURE_DOWN)
pump.controller.smart_initialize()
robot.CLEAN_HEAD_DISH.set_angle(CLEAN_HEAD_DISH_UP)
robot.CLEAN_HEAD_MIXTURE.home()
