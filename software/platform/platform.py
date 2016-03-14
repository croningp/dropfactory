from commanduino import CommandManager
from commanduino.devices.axis import Axis, MultiAxis

import logging
logging.basicConfig(level=logging.INFO)

cmdMng = CommandManager.from_configfile('./platform_config.json')


X = Axis(cmdMng.X, 0.00935, 0, 350)
Y = Axis(cmdMng.Y, 0.00935, 0, 200)
Z = Axis(cmdMng.Z, 0.00125, 0, 156)
G1 = cmdMng.G1
G2 = cmdMng.G2

XY = MultiAxis(X, Y)


def home():
    Z.home()
    XY.home()

1645
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
