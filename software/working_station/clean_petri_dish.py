import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

from tools.tasks import Task


CLEAN_HEAD_UP = 50
CLEAN_HEAD_DOWN = 20

INLET = 'E'
OUTLET = 'I'

VOLUME_DISH = 3.5
VOLUME_WASTE_SHORT = 5
VOLUME_WASTE_LONG = 10


class CleanPetriDish(Task):

    def __init__(self, clean_head, waste_pump, water_pump, acetone_pump):
        Task.__init__(self)
        self.clean_head = clean_head
        self.waste_pump = waste_pump
        self.water_pump = water_pump
        self.acetone_pump = acetone_pump
        self.start()

    def wait_until_pumps_idle(self):
        self.waste_pump.wait_until_idle()
        self.water_pump.wait_until_idle()
        self.acetone_pump.wait_until_idle()

    def main(self):
        # put the head down
        self.clean_head.set_angle(CLEAN_HEAD_DOWN)

        # suck what is there and fill syringes
        self.waste_pump.pump(VOLUME_WASTE_SHORT ,from_valve=OUTLET)
        # self.water_pump.pump(VOLUME_DISH ,from_valve=INLET)
        self.acetone_pump.pump(VOLUME_DISH ,from_valve=INLET)

        # fill with acetone while flushing waste
        self.wait_until_pumps_idle()
        self.acetone_pump.deliver(VOLUME_DISH ,to_valve=OUTLET)
        self.waste_pump.deliver(VOLUME_WASTE_SHORT ,to_valve=INLET)

        # empty dish
        self.wait_until_pumps_idle()
        self.waste_pump.pump(VOLUME_WASTE_LONG ,from_valve=OUTLET)

        # put the head up and flush waste
        self.wait_until_pumps_idle()
        self.clean_head.set_angle(CLEAN_HEAD_UP)
        self.waste_pump.deliver(VOLUME_WASTE_LONG ,to_valve=INLET, wait=True)
