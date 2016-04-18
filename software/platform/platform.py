from commanduino import CommandManager
from commanduino.devices.axis import Axis, MultiAxis

import logging
logging.basicConfig(level=logging.INFO)

cmdMng = CommandManager.from_configfile('./platform_config.json')

MICROSTEP = 32.0
LINEAR_STEPPER_UNIT_PER_STEP = 0.0508  # mm/step
SYRINGUE_UNIT_PER_MM =  80 / 47.70 #  47.70mm for 80ul

X = Axis(cmdMng.X, 0.00935, 0, 350)
Y = Axis(cmdMng.Y, 0.00935, 0, 200)
Z = Axis(cmdMng.Z, 0.00125, 0, 156)
XY = MultiAxis(X, Y)

GENEVA_DISH = cmdMng.G1
GENEVA_MIXTURE = cmdMng.G2

SYRINGE = Axis(cmdMng.S1, LINEAR_STEPPER_UNIT_PER_STEP * SYRINGUE_UNIT_PER_MM / MICROSTEP, 0, 96)
CLEAN_HEAD_DISH = cmdMng.S3
CLEAN_HEAD_MIXTURE = Axis(cmdMng.S2, LINEAR_STEPPER_UNIT_PER_STEP / MICROSTEP, 0, 38)

STIRRER = cmdMng.A1


def home():
    Z.home()
    XY.home()
    SYRINGE.home()
    CLEAN_HEAD_MIXTURE.home()

def rotate_geneva_wheels():
    N_STEPS = 200
    GENEVA_DISH.move(-N_STEPS * MICROSTEP, wait=False)
    GENEVA_MIXTURE.move(N_STEPS * MICROSTEP, wait=False)
    GENEVA_DISH.wait_until_idle()
    GENEVA_MIXTURE.wait_until_idle()
