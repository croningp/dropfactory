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
from constants import Z_FREE_LEVEL
from constants import XY_ABOVE_VIAL

from constants import TUBE_OIL_VOLUME

SLEEP_TIME = 0.1

OUTLET_WASTE = 'E'
INLET_WASTE_TUBE = 'O'
INLET_WASTE_VIAL = 'I'

INLET_ACETONE = 'E'
OUTLET_ACETONE_TUBE = 'I'
OUTLET_ACETONE_VIAL = 'O'

# vial cleaning
WASTE_RATIO = 2.0
VOLUME_VIAL_FIRST = 1.5
VOLUME_VIAL_SECOND = 2.5
VOLUME_VIAL_THIRD = 1.0

SYRINGE_IN_ACETONE_LEVEL = 147

SYRINGE_FILL_AIR_VOLUME = 50  # uL
SYRINGE_FILL_ACETONE_VOLUME = 100  # uL

N_REPEAT_SYRINGE_ACETONE = 3
N_REPEAT_SYRINGE_AIR = 8

# tube cleaning
VOLUME_TUBE = 0.7
VOLUME_EMPTY_TUBE = 2
N_WASH_TUBE = 5
FLUSH_SPEED = 12000


class CleanOilParts(Task):

    def __init__(self, xy_axis, z_axis, syringe, clean_head, waste_pump, acetone_pump):
        Task.__init__(self)
        self.clean_syringe_station = CleanSyringe(xy_axis, z_axis, syringe, waste_pump, acetone_pump)
        self.clean_tube_station = CleanTube(clean_head, waste_pump, acetone_pump)
        self.start()

    def launch(self, XP_dict, clean_tube=True, clean_syringe=True):
        self.XP_dict = XP_dict
        self.clean_tube = clean_tube
        self.clean_syringe = clean_syringe
        self.running = True

    def get_added_waste_volume(self):
        added_waste_volume = 0
        if self.clean_tube:
            if self.XP_dict is not None:
                if 'formulation' in self.XP_dict:
                    added_waste_volume += TUBE_OIL_VOLUME  # this is the volume of oil dispensed
            for _ in range(N_WASH_TUBE):
                added_waste_volume += VOLUME_TUBE

        if self.clean_syringe:
            # we neglect oil volume remaining in syringe, shoudl be included in clean_tube already
            added_waste_volume += VOLUME_VIAL_FIRST
            added_waste_volume += VOLUME_VIAL_SECOND
            added_waste_volume += VOLUME_VIAL_THIRD

        return added_waste_volume

    def main(self):
        # The problem is that tube and syringe clean share the same pump..

        if self.clean_syringe:
            # fill vials with acetone
            self.clean_syringe_station.fill_vial(VOLUME_VIAL_FIRST, VOLUME_VIAL_SECOND)  # this is blocking
            # clean syringe in background thread
            self.clean_syringe_station.start_cleaning_syringe_step()

        if self.clean_tube:
            # start cleaning tube in background thread
            self.clean_tube_station.launch(self.XP_dict)

        if self.clean_syringe:
            # when cleaning syringe step is over: dry syringe and empty vials
            self.clean_syringe_station.wait_until_idle()
            self.clean_syringe_station.start_drying_syringe_step()

        if self.clean_tube:
            # when tube is clean
            self.clean_tube_station.wait_until_idle()

        if self.clean_syringe:
            # empty vial and clean it
            self.clean_syringe_station.final_clean_vial(VOLUME_VIAL_SECOND, VOLUME_VIAL_THIRD)  # this is blocking
            # wait before closing
            self.clean_syringe_station.wait_until_idle()


class CleanSyringe(threading.Thread):

    def __init__(self, xy_axis, z_axis, syringe, waste_pump, acetone_pump):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.filling_vial = False
        self.cleaning_syringe = False
        self.drying_syringe = False

        self.xy_axis = xy_axis
        self.z_axis = z_axis
        self.syringe = syringe
        self.waste_pump = waste_pump
        self.acetone_pump = acetone_pump

        self.start()

    def run(self):
        self.interrupted.acquire()
        while self.interrupted.locked():
            if self.cleaning_syringe:
                self.clean_syringe()
                self.cleaning_syringe = False
            elif self.drying_syringe:
                self.dry_syringe()
                self.drying_syringe = False
            else:
                time.sleep(SLEEP_TIME)

    def stop(self):
        self.interrupted.release()

    def wait_until_idle(self):
        while self.cleaning_syringe or self.drying_syringe:
            time.sleep(SLEEP_TIME)

    def fill_vial(self, first_volume_in_ml, second_volume_in_ml):
        # wait for stuff to be ready
        self.xy_axis.wait_until_idle()
        self.acetone_pump.wait_until_idle()

        # we raise an error instead of going to the level, because we can not assume where the head is, the user should be smart and this is the only protection we can implement
        if self.z_axis.get_current_position() > Z_FREE_LEVEL:
            raise Exception('Syringe is too low!!!')

        # pump acetone
        self.acetone_pump.pump(first_volume_in_ml, from_valve=INLET_ACETONE)

        # move above vial
        self.xy_axis.move_to(XY_ABOVE_VIAL, wait=False)
        self.z_axis.move_to(Z_FREE_LEVEL, wait=False)

        # deliver acetone
        self.acetone_pump.wait_until_idle()
        self.acetone_pump.deliver(first_volume_in_ml, to_valve=OUTLET_ACETONE_VIAL, wait=False)

        # empty syringe with potential oil inside
        self.xy_axis.wait_until_idle()
        self.z_axis.wait_until_idle()
        self.syringe.go_to_volume(0, wait=True)

        # we remove the acetone with the dirt from syringe, and put more fresh acetone back in
        self.waste_pump.wait_until_idle()
        self.acetone_pump.wait_until_idle()

        self.waste_pump.pump(WASTE_RATIO * first_volume_in_ml, from_valve=INLET_WASTE_VIAL)
        self.acetone_pump.pump(second_volume_in_ml, from_valve=INLET_ACETONE)

        self.waste_pump.wait_until_idle()
        self.acetone_pump.wait_until_idle()

        self.flush_waste(wait=False)
        self.acetone_pump.deliver(second_volume_in_ml, to_valve=OUTLET_ACETONE_VIAL)

        self.waste_pump.wait_until_idle()
        self.acetone_pump.wait_until_idle()

    def empty_vial(self, volume_in_ml):
        self.waste_pump.wait_until_idle()
        self.waste_pump.pump(volume_in_ml, from_valve=INLET_WASTE_VIAL, wait=True)
        self.flush_waste(wait=True)

    def flush_waste(self, wait=True):
        self.waste_pump.set_valve_position(OUTLET_WASTE)
        self.waste_pump.go_to_volume(0, speed=FLUSH_SPEED, wait=wait)

    def final_clean_vial(self, current_volume_in_ml, final_volume_in_ml):
        self.acetone_pump.pump(final_volume_in_ml, from_valve=INLET_ACETONE)
        self.empty_vial(WASTE_RATIO * current_volume_in_ml)

        self.acetone_pump.wait_until_idle()
        self.acetone_pump.deliver(final_volume_in_ml, to_valve=OUTLET_ACETONE_VIAL)

        self.acetone_pump.wait_until_idle()
        self.waste_pump.pump(WASTE_RATIO * final_volume_in_ml, from_valve=INLET_WASTE_VIAL, wait=True)
        self.flush_waste(wait=True)

    def start_cleaning_syringe_step(self):
        self.cleaning_syringe = True

    def clean_syringe(self):
        # wait for stuff to be ready
        self.xy_axis.wait_until_idle()
        self.z_axis.wait_until_idle()
        self.syringe.wait_until_idle()

        # move above vial
        # we raise an error instead of going to the level, because we can not assume where the head is, the user should be smart and this is the only protection we can implement
        if self.z_axis.get_current_position() > Z_FREE_LEVEL:
            raise Exception('Syringe is too low!!!')

        # move in vial
        # this is already done in fill vial step, but this is to make sure it works stand alone mode too
        self.xy_axis.move_to(XY_ABOVE_VIAL)
        self.z_axis.move_to(Z_FREE_LEVEL)
        self.syringe.go_to_volume(0, wait=False)

        # go into acetone
        self.z_axis.move_to(SYRINGE_IN_ACETONE_LEVEL)
        self.syringe.wait_until_idle()

        # flush acetone into it
        for _ in range(N_REPEAT_SYRINGE_ACETONE):
            self.syringe.pump(SYRINGE_FILL_ACETONE_VOLUME)
            self.syringe.deliver(SYRINGE_FILL_ACETONE_VOLUME)

        # go up
        self.z_axis.move_to(Z_FREE_LEVEL)

    def start_drying_syringe_step(self):
        self.drying_syringe = True

    def dry_syringe(self):
        # wait for stuff to be ready
        self.syringe.wait_until_idle()

        # flush air into the syringe
        for _ in range(N_REPEAT_SYRINGE_AIR):
            self.syringe.pump(SYRINGE_FILL_AIR_VOLUME)
            self.syringe.deliver(SYRINGE_FILL_AIR_VOLUME)


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
        if self.clean_head.get_switch_state():
            raise Exception('Clean head oil mixture did not go down, stepper might be broken...')

    def raise_cleaning_head(self):
        self.clean_head.home()

    def empty_tube(self, volume_in_ml=VOLUME_EMPTY_TUBE):
        self.waste_pump.pump(volume_in_ml, from_valve=INLET_WASTE_TUBE)

    def flush_waste(self):
        self.waste_pump.set_valve_position(OUTLET_WASTE)
        self.waste_pump.go_to_volume(0, speed=FLUSH_SPEED)

    def load_acetone(self, volume_in_ml):
        self.acetone_pump.pump(volume_in_ml, from_valve=INLET_ACETONE)

    def deliver_acetone_to_tube(self):
        self.acetone_pump.deliver(VOLUME_TUBE, to_valve=OUTLET_ACETONE_TUBE)

    def main(self):
        # wait stuff ready
        self.clean_head.wait_until_idle()
        self.wait_until_pumps_idle()

        # load acetone while lowering head
        self.load_acetone(N_WASH_TUBE * VOLUME_TUBE)  # loading acetone for several wash (N_WASH_TUBE)
        self.lower_cleaning_head()  # this is blocking

        # start cleaning cycle when pump loaded
        self.wait_until_pumps_idle()
        self.empty_tube()

        # poor acetone and empty
        for _ in range(N_WASH_TUBE):
            self.wait_until_pumps_idle()
            self.deliver_acetone_to_tube()

            self.wait_until_pumps_idle()
            self.empty_tube()

        # flush waste
        self.wait_until_pumps_idle()
        self.flush_waste()

        self.raise_cleaning_head()  # this is blocking
        self.wait_until_pumps_idle()  # to ensure waste finished flushing
