import os
import time
import threading

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

from tools.tasks import Task
from constants import CLEAN_HEAD_MIXTURE_DOWN
from constants import SYRINGE_MAX

SLEEP_TIME = 0.1

OUTLET_WASTE = 'E'
INLET_WASTE_TUBE = 'O'
INLET_WASTE_VIAL = 'I'

INLET_ACETONE = 'E'
OUTLET_ACETONE_TUBE = 'I'
OUTLET_ACETONE_VIAL = 'O'

# vial cleaning
VOLUME_VIAL = 2.5
VOLUME_EMPTY_VIAL = 5

XY_ABOVE_VIAL = [95, 15]
SYRINGE_ABOVE_VIAL_LEVEL = 110
SYRINGE_IN_ACETONE_LEVEL = 147
SYRINGE_EMPTY_LEVEL = SYRINGE_MAX
SYRINGE_FILL_LEVEL = SYRINGE_MAX - 100  # 100uL
N_REPEAT_SYRINGE_ACETONE = 2
N_REPEAT_SYRINGE_AIR = 5

# tube cleaning
VOLUME_TUBE = 0.6
VOLUME_EMPTY_TUBE = 2
N_WASH_TUBE = 5

class CleanOilParts(Task):

    def __init__(self, xy_axis, z_axis, syringe, clean_head, waste_pump, acetone_pump):
        Task.__init__(self)
        self.clean_syringe = CleanSyringe(xy_axis, z_axis, syringe, waste_pump, acetone_pump)
        self.clean_tube = CleanTube(clean_head, waste_pump, acetone_pump)
        self.start()

    def main(self):
        # The problem is that tube and syringe clean share the same pump..

        # fill vials with acetone
        self.clean_syringe.start_fill_vial_step()
        self.clean_syringe.wait_until_idle()

        # start cleaning syringe while cleaning oils
        self.clean_syringe.start_cleaning_syringe_step()
        self.clean_tube.launch(self.XP_dict)
        self.clean_tube.wait_until_idle()
        self.clean_syringe.wait_until_idle()

        # empty vials
        self.clean_syringe.start_empty_vial_step()
        self.clean_syringe.wait_until_idle()

class CleanSyringe(threading.Thread):

    def __init__(self, xy_axis, z_axis, syringe, waste_pump, acetone_pump):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.filling_vial = False
        self.emptying_vial = False
        self.cleaning_syringe = False

        self.xy_axis = xy_axis
        self.z_axis = z_axis
        self.syringe = syringe
        self.waste_pump = waste_pump
        self.acetone_pump = acetone_pump

        self.start()

    def run(self):
        self.interrupted.acquire()
        while self.interrupted.locked():
            if self.filling_vial:
                self.fill_vial()
                self.filling_vial = False
            elif self.emptying_vial:
                self.empty_vial()
                self.emptying_vial = False
            elif self.cleaning_syringe:
                self.clean_syringe()
                self.cleaning_syringe = False
            else:
                time.sleep(SLEEP_TIME)

    def wait_until_idle(self):
        while self.filling_vial or self.emptying_vial or self.cleaning_syringe:
            time.sleep(SLEEP_TIME)

    def start_fill_vial_step(self):
        self.filling_vial = True

    def fill_vial(self):
        self.acetone_pump.wait_until_idle()
        self.acetone_pump.pump(VOLUME_VIAL ,from_valve=INLET_ACETONE, wait=True)
        self.acetone_pump.deliver(VOLUME_VIAL ,to_valve=OUTLET_ACETONE_VIAL, wait=True)

    def start_empty_vial_step(self):
        self.emptying_vial = True

    def empty_vial(self):
        self.waste_pump.wait_until_idle()
        self.waste_pump.pump(VOLUME_EMPTY_VIAL, from_valve=INLET_WASTE_VIAL, wait=True)
        self.waste_pump.deliver(VOLUME_EMPTY_VIAL ,to_valve=OUTLET_WASTE, wait=True)

    def start_cleaning_syringe_step(self):
        self.cleaning_syringe = True

    def clean_syringe(self):
        # we raise an error binstead of going to the level, because we can not assume where the head is, the user should be smart and this is the only protection we can implement
        if self.z_axis.get_current_position() > SYRINGE_ABOVE_VIAL_LEVEL:
            raise Exception('Syringe is too low!!!')

        # move syringe into vials
        self.xy_axis.move_to(XY_ABOVE_VIAL)
        self.z_axis.move_to(SYRINGE_IN_ACETONE_LEVEL)

        # emoty syringe
        self.syringe.move_to(SYRINGE_EMPTY_LEVEL)

        # flush acetone into it
        for _ in range(N_REPEAT_SYRINGE_ACETONE):
            self.syringe.move_to(SYRINGE_FILL_LEVEL)
            self.syringe.move_to(SYRINGE_EMPTY_LEVEL)

        # go up
        self.z_axis.move_to(SYRINGE_ABOVE_VIAL_LEVEL)

        # flush air into it
        for _ in range(N_REPEAT_SYRINGE_AIR):
            self.syringe.move_to(SYRINGE_FILL_LEVEL)
            self.syringe.move_to(SYRINGE_EMPTY_LEVEL)


class CleanTube(Task):

    def __init__(self, clean_head, waste_pump, acetone_pump):
        Task.__init__(self)
        self.clean_head = clean_head
        self.waste_pump = waste_pump
        self.acetone_pump = acetone_pump
        self.start()

    def wait_until_pumps_idle(self):
        self.waste_pump.wait_until_idle()
        self.acetone_pump.wait_until_idle()

    def lower_cleaning_head(self):
        self.clean_head.move_to(CLEAN_HEAD_MIXTURE_DOWN)

    def raise_cleaning_head(self):
        self.clean_head.home()

    def empty_tube(self, volume_in_ml=VOLUME_EMPTY_TUBE):
        self.waste_pump.pump(volume_in_ml, from_valve=INLET_WASTE_TUBE)

    def flush_waste(self):
        self.waste_pump.set_valve_position(OUTLET_WASTE)
        self.waste_pump.go_to_volume(0)

    def load_acetone(self, volume_in_ml):
        self.acetone_pump.pump(volume_in_ml ,from_valve=INLET_ACETONE)

    def deliver_acetone_to_tube(self):
        self.acetone_pump.deliver(VOLUME_TUBE ,to_valve=OUTLET_ACETONE_TUBE)

    def main(self):
        self.load_acetone(N_WASH_TUBE * VOLUME_TUBE)
        self.lower_cleaning_head()

        self.wait_until_pumps_idle()
        self.empty_tube()

        for _ in range(N_WASH_TUBE):
            self.wait_until_pumps_idle()
            self.deliver_acetone_to_tube()

            self.wait_until_pumps_idle()
            self.empty_tube()

        self.wait_until_pumps_idle()
        self.flush_waste()

        self.raise_cleaning_head()
        self.wait_until_pumps_idle()
