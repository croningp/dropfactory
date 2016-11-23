import os
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

import logging
logging.basicConfig(level=logging.INFO)

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

import time

from constants import CLEAN_HEAD_MIXTURE_MAX
from constants import CLEAN_HEAD_DISH_MAX
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

CLEAN_HEAD_MIXTURE = Axis(cmdMng.S2, LINEAR_STEPPER_UNIT_PER_STEP / MICROSTEP, 0, CLEAN_HEAD_MIXTURE_MAX)

CLEAN_HEAD_DISH = Axis(cmdMng.S3, LINEAR_STEPPER_UNIT_PER_STEP / MICROSTEP, 0, CLEAN_HEAD_DISH_MAX)

FILL_HEAD_MIXTURE = Axis(cmdMng.S4, LINEAR_STEPPER_UNIT_PER_STEP / MICROSTEP, 0, FILL_HEAD_MIXTURE_MAX)

TEMPERATURE_SENSOR = cmdMng.SHT15

GENEVA_TIMEOUT = 30
SLEEP_TIME = 0.5


def init(user_query=True, init_syringe=True, init_syringe_above_vial=True, init_geneva_wheel=True):
    # order is really important here!
    if user_query:
        raw_input('\n### Robot initialization:\nMake sure the syringe and xyz system can go init safely, then press enter')
    CLEAN_HEAD_MIXTURE.home(wait=False)
    CLEAN_HEAD_DISH.home(wait=False)
    FILL_HEAD_MIXTURE.home(wait=False)
    # while other stuff homing, move z up to home
    Z.home()  # blocking
    # when z up, move xy home
    XY.home()
    # wait all other stuff finished
    CLEAN_HEAD_MIXTURE.wait_until_idle()
    CLEAN_HEAD_DISH.wait_until_idle()
    FILL_HEAD_MIXTURE.wait_until_idle()

    # we do this here because moving the Z axis and the syringe creates vibration that disturb the image acquisition
    if init_syringe:
        SYRINGE.home(wait=False)

    # init geneva wheel
    if init_geneva_wheel:
        GENEVA_DISH.home(wait=False)
        GENEVA_MIXTURE.home(wait=False)
        GENEVA_DISH.wait_until_idle()
        GENEVA_MIXTURE.wait_until_idle()

    if init_syringe:
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
    if not CLEAN_HEAD_MIXTURE.get_switch_state():
        raise Exception('Cannot rotate geneva wheels, cleaning head mixture is not home')

    if not CLEAN_HEAD_DISH.get_switch_state():
        raise Exception('Cannot rotate geneva wheels, cleaning head dish is not in up position')

    if not FILL_HEAD_MIXTURE.get_switch_state():
        raise Exception('Cannot rotate geneva wheels, filling head mixture is not home')

    # we move a bit until the end stop are relased, then we home (thus turn until it touch the end stops)
    # bootstrap wheel
    bootstrap_geneva_wheel()
    # home
    GENEVA_DISH.home(wait=False)
    GENEVA_MIXTURE.home(wait=False)

    start_time = time.time()
    while GENEVA_DISH.is_moving or GENEVA_MIXTURE.is_moving:
        time.sleep(SLEEP_TIME)

        elapsed = time.time() - start_time
        if elapsed > GENEVA_TIMEOUT:
            GENEVA_DISH.stop()
            GENEVA_MIXTURE.stop()
            raise Exception('Geneva wheels seem to not be moving, please check what is happening')



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
