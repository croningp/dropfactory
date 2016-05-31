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
VOLUME_WASTE = 5
FINAL_VOLUME_WASTE = 10

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
        self.clean_head.set_angle(CLEAN_HEAD_DOWN)

    def raise_cleaning_head(self):
        self.clean_head.set_angle(CLEAN_HEAD_UP)

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

    def main(self):
        # put the head down
        self.lower_cleaning_head()

        # suck what is there and fill syringes
        self.wait_until_pumps_idle()
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
