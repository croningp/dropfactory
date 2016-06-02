import os
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

import logging
logging.basicConfig(level=logging.INFO)

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

from constants import CLEAN_HEAD_MIXTURE_MAX
from constants import CLEAN_HEAD_DISH_UP
from constants import XY_ABOVE_VIAL
from constants import Z_FREE_LEVEL

from commanduino import CommandManager
from commanduino.devices.axis import Axis, MultiAxis
from syringe import Syringe

configfile = os.path.join(HERE_PATH, 'robot_config.json')
cmdMng = CommandManager.from_configfile(configfile)

MICROSTEP = 32.0
LINEAR_STEPPER_UNIT_PER_STEP = 0.05  #08  # mm/step
SYRINGUE_UNIT_PER_MM =  250 / 59.70 #  59.70mm for 250ul

X = Axis(cmdMng.X, 0.00935, 0, 160)
Y = Axis(cmdMng.Y, 0.00935, 0, 100)
Z = Axis(cmdMng.Z, 0.00125, 0, 156)
XY = MultiAxis(X, Y)

GENEVA_DISH = cmdMng.G1
GENEVA_MIXTURE = cmdMng.G2

SYRINGE_MAX = 235
SYRINGE_AXIS = Axis(cmdMng.S1, LINEAR_STEPPER_UNIT_PER_STEP * SYRINGUE_UNIT_PER_MM / MICROSTEP, 0, SYRINGE_MAX)
SYRINGE = Syringe(SYRINGE_AXIS, SYRINGE_MAX)

CLEAN_HEAD_DISH = cmdMng.S3

CLEAN_HEAD_MIXTURE = Axis(cmdMng.S2, LINEAR_STEPPER_UNIT_PER_STEP / MICROSTEP, 0, CLEAN_HEAD_MIXTURE_MAX)

STIRRER = cmdMng.A1


def init():
    # order is really important here!
    raw_input('\n### Robot initialization:\nMake sure the syringe and xyz system can go init safely, then press enter')
    SYRINGE.home(wait=False)
    CLEAN_HEAD_MIXTURE.home(wait=False)
    CLEAN_HEAD_DISH.set_angle(CLEAN_HEAD_DISH_UP)
    Z.home()
    XY.home()
    CLEAN_HEAD_MIXTURE.wait_until_idle()
    SYRINGE.wait_until_idle()
    response = raw_input('## Do you want to empty the syringe in the vial [y/N]: ')
    if response in ['y', 'Y']:
        XY.move_to(XY_ABOVE_VIAL)
        Z.move_to(Z_FREE_LEVEL)
    SYRINGE.init()


def rotate_geneva_wheels():
    mixture_head_position = CLEAN_HEAD_MIXTURE.get_current_position()
    if mixture_head_position != 0:
        raise Exception('Cannot rotate geneva wheels, cleaning head mixture is not home')

    dish_head_position = CLEAN_HEAD_DISH.get_angle()
    if dish_head_position != CLEAN_HEAD_DISH_UP:
        raise Exception('Cannot rotate geneva wheels, cleaning head dish is not in up position')

    N_STEPS = 200
    GENEVA_DISH.move(-N_STEPS * MICROSTEP, wait=False)
    GENEVA_MIXTURE.move(N_STEPS * MICROSTEP, wait=False)
    GENEVA_DISH.wait_until_idle()
    GENEVA_MIXTURE.wait_until_idle()
