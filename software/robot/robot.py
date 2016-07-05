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
from constants import FILL_HEAD_MIXTURE_MAX
from constants import XY_ABOVE_VIAL
from constants import Z_FREE_LEVEL

from commanduino import CommandManager
from commanduino.devices.axis import Axis, MultiAxis
from syringe import Syringe

configfile = os.path.join(HERE_PATH, 'robot_config.json')
cmdMng = CommandManager.from_configfile(configfile)

MICROSTEP = 32.0
LINEAR_STEPPER_UNIT_PER_STEP = 0.05  # 08  # mm/step
SYRINGUE_UNIT_PER_MM = 250 / 59.70  # 59.70mm for 250ul

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
CLEAN_HEAD_DISH_SWITCH = cmdMng.D1

CLEAN_HEAD_MIXTURE = Axis(cmdMng.S2, LINEAR_STEPPER_UNIT_PER_STEP / MICROSTEP, 0, CLEAN_HEAD_MIXTURE_MAX)

FILL_HEAD_MIXTURE = Axis(cmdMng.S4, LINEAR_STEPPER_UNIT_PER_STEP / MICROSTEP, 0, FILL_HEAD_MIXTURE_MAX)

STIRRER = cmdMng.A1


def init(user_query=True, init_syringe=True, init_syringe_above_vial=True, init_geneva_wheel=True):
    # order is really important here!
    if user_query:
        raw_input('\n### Robot initialization:\nMake sure the syringe and xyz system can go init safely, then press enter')
    if init_syringe:
        SYRINGE.home(wait=False)
    CLEAN_HEAD_MIXTURE.home(wait=False)
    FILL_HEAD_MIXTURE.home(wait=False)
    CLEAN_HEAD_DISH.set_angle(CLEAN_HEAD_DISH_UP)
    # while other stuff homing, move z up to home
    Z.home()  # blocking
    # when z up, move xy home
    XY.home()
    # wait all other stuff finished
    FILL_HEAD_MIXTURE.wait_until_idle()
    CLEAN_HEAD_MIXTURE.wait_until_idle()
    # init geneva wheel
    if init_geneva_wheel:
        GENEVA_DISH.home(wait=False)
        GENEVA_MIXTURE.home(wait=False)
        GENEVA_DISH.wait_until_idle()
        GENEVA_MIXTURE.wait_until_idle()
    #
    if init_syringe:
        # init syringe to zero level
        SYRINGE.wait_until_idle()

        if user_query:
            response = raw_input('## Do you want to empty the syringe in the vial [y/N]: ')
            if response in ['y', 'Y']:
                init_syringe_above_vial = True
            else:
                init_syringe_above_vial = False
        #
        if init_syringe_above_vial:
            XY.move_to(XY_ABOVE_VIAL)
            Z.move_to(Z_FREE_LEVEL)
        SYRINGE.init()


def rotate_geneva_wheels():
    clean_mixture_head_position = CLEAN_HEAD_MIXTURE.get_current_position()
    if clean_mixture_head_position != 0:
        raise Exception('Cannot rotate geneva wheels, cleaning head mixture is not home')

    dish_head_position = CLEAN_HEAD_DISH.get_angle()
    if dish_head_position != CLEAN_HEAD_DISH_UP:
        raise Exception('Cannot rotate geneva wheels, cleaning head dish is not in up position')

    fill_mixture_head_position = FILL_HEAD_MIXTURE.get_current_position()
    if fill_mixture_head_position != 0:
        raise Exception('Cannot rotate geneva wheels, filling head mixture is not home')

    if not CLEAN_HEAD_DISH_SWITCH.get_state():  # True when switch not pressed
        raise Exception('Cannot rotate geneva wheels, the dish cleaning head does not seems to be up')

    # we move a bit until the end stop are relased, then we home (thus turn until it touch the end stops)

    # bootstrap wheel
    bootstrap_geneva_wheel()
    # home
    GENEVA_DISH.home(wait=False)
    GENEVA_MIXTURE.home(wait=False)
    # wait
    GENEVA_DISH.wait_until_idle()
    GENEVA_MIXTURE.wait_until_idle()


def bootstrap_geneva_wheel():

    # bootstrap
    N_BOOTSTRAP_STEPS = - 20 * MICROSTEP

    # check wheel status
    is_geneva_dish_home = GENEVA_DISH.get_switch_state()
    is_geneva_mixture_home = GENEVA_MIXTURE.get_switch_state()

    count = 0
    while is_geneva_dish_home or is_geneva_mixture_home:

        if is_geneva_dish_home:
            GENEVA_DISH.move(N_BOOTSTRAP_STEPS, wait=False)

        if is_geneva_mixture_home:
            GENEVA_MIXTURE.move(N_BOOTSTRAP_STEPS, wait=False)

        # wait
        GENEVA_DISH.wait_until_idle()
        GENEVA_MIXTURE.wait_until_idle()

        # check status again
        is_geneva_dish_home = GENEVA_DISH.get_switch_state()
        is_geneva_mixture_home = GENEVA_MIXTURE.get_switch_state()

        #
        count += 1
        if count > 10:
            raise Exception('Geneva wheels seem to not be moving, please check what is happening')
