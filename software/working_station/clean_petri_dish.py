import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

import time

from tools.tasks import Task
from constants import CLEAN_HEAD_DISH_DOWN

INLET = 'O'
OUTLET = 'I'

VOLUME_DISH = 4.5
VOLUME_WASTE = 7
FINAL_VOLUME_WASTE = 10

SLEEP_TIME_CHECK_HEAD_SWITCH = 1

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

    def lower_cleaning_head(self):
        self.clean_head.move_to(CLEAN_HEAD_DISH_DOWN, wait=True)

    def raise_cleaning_head(self):
        self.clean_head.home()

    def empty_dish(self, volume_in_ml=VOLUME_WASTE):
        self.waste_pump.pump(volume_in_ml, from_valve=OUTLET)

    def flush_waste(self):
        self.waste_pump.set_valve_position(INLET)
        self.waste_pump.go_to_volume(0)

    def load_water(self):
        self.water_pump.pump(VOLUME_DISH ,from_valve=INLET)

    def deliver_water(self):
        self.water_pump.deliver(VOLUME_DISH ,to_valve=OUTLET)

    def load_acetone(self):
        self.acetone_pump.pump(VOLUME_DISH ,from_valve=INLET)

    def deliver_acetone(self):
        self.acetone_pump.deliver(VOLUME_DISH ,to_valve=OUTLET)

    def get_added_waste_volume(self):
        added_waste_volume = 0
        if self.XP_dict is not None:
            if 'surfactant_volume' in self.XP_dict:
                added_waste_volume += self.XP_dict['surfactant_volume'] # we suck surfactant first
            added_waste_volume += VOLUME_DISH * 4  # 1 acetone, 1 water, 2 acetone
        return added_waste_volume

    def main(self):
        # wait stuff ready
        self.clean_head.wait_until_idle()
        self.wait_until_pumps_idle()

        # put the head down
        self.lower_cleaning_head()

        # suck what is there and fill syringes
        self.load_water()
        self.load_acetone()
        self.empty_dish()

        # fill with acetone while flushing waste
        self.wait_until_pumps_idle()
        self.deliver_acetone()
        self.flush_waste()

        # empty dish and reload acetone
        self.wait_until_pumps_idle()
        self.load_acetone()
        self.empty_dish()

        # fill with water while flushing waste
        self.wait_until_pumps_idle()
        self.deliver_water()
        self.flush_waste()

        # empty dish and reload acetone
        self.wait_until_pumps_idle()
        self.empty_dish()

        # fill with acetone while flushing waste
        self.wait_until_pumps_idle()
        self.deliver_acetone()
        self.flush_waste()

        # empty dish and reload acetone
        self.wait_until_pumps_idle()
        self.load_acetone()
        self.empty_dish()

        # fill with acetone while flushing waste
        self.wait_until_pumps_idle()
        self.deliver_acetone()
        self.flush_waste()

        # empty dish and reload acetone
        self.wait_until_pumps_idle()
        self.empty_dish(FINAL_VOLUME_WASTE)

        # put the head up and flush waste
        self.wait_until_pumps_idle()
        self.flush_waste()
        self.raise_cleaning_head()

        # wait all is over before returning
        self.wait_until_pumps_idle()
