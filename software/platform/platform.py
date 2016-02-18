from commanduino import CommandManager
from commanduino.devices.axis import Axis, MultiAxis

import logging
logging.basicConfig(level=logging.INFO)

cmdMng = CommandManager.from_configfile('./platform_config.json')


X = Axis(cmdMng.X, 1, 0, 55000)
Y = Axis(cmdMng.Y, 1, 0, 30000)
Z = Axis(cmdMng.Z, 1, 0, 48000)
G1 = cmdMng.G1
G2 = cmdMng.G2

XY = MultiAxis(X, Y)


def home():
    Z.home()
    XY.home()


def cycle():
    XY.move_to([16700, 11200])
    Z.move_to([38000])
    Z.move_to([25000])
    XY.move_to([25500, 11200])
    Z.move_to([45000])
    Z.move_to([25000])
    G1.move(32 * 200, wait=False)
    G2.move(32 * 200, wait=True)


def main():
    home()
    for _ in range(10):
        cycle()
