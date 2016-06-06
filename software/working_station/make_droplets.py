import os
import time
import threading

import numpy as np

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

from constants import Z_FREE_LEVEL
from constants import XY_ABOVE_TUBE
from constants import XY_ABOVE_DISH

SLEEP_TIME = 0.1

Z_SYRINGE_IN_OIL = 140
Z_ABOVE_SURFACTANT = 135
Z_AT_SURFACTANT = 142

SYRINGE_PRACTICAL_VOLUME = 200  # uL
SYRINGE_BUFFER_VOLUME = 20  # this a buffer volume reference in addition of the droplets volume, we will use twice that

MAX_DIST_TO_CENTER_DROPLET = 20  # mm


class MakeDroplets(threading.Thread):

    def __init__(self, xy_axis, z_axis, syringe):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.filling_syringe = False

        self.xy_axis = xy_axis
        self.z_axis = z_axis
        self.syringe = syringe

        self.start()

    def run(self):
        self.interrupted.acquire()
        while self.interrupted.locked():
            if self.filling_syringe:
                self.fill_syringe()
                self.filling_syringe = False
            else:
                time.sleep(SLEEP_TIME)

    def stop(self):
        self.interrupted.release()

    def wait_until_idle(self):
        while self.filling_syringe:
            time.sleep(SLEEP_TIME)

    def is_droplet_position_valid(self, droplet_position):
        return np.linalg.norm(droplet_position) <= MAX_DIST_TO_CENTER_DROPLET

    def load_XP(self, XP_dict):
        self.droplet_list = XP_dict['droplets']

        total_volume = 2 * SYRINGE_BUFFER_VOLUME
        for droplet_info in self.droplet_list:
            total_volume += droplet_info['volume']

        self.oil_volume_to_pump = total_volume

    def start_filling_syringe_step(self):
        self.filling_syringe = True

    def fill_syringe(self):
        # wait for stuff to be ready
        self.xy_axis.wait_until_idle()
        self.z_axis.wait_until_idle()
        self.syringe.wait_until_idle()

        # we raise an error instead of going to the level, because we can not assume where the head is, the user should be smart and this is the only protection we can implement
        if self.z_axis.get_current_position() > Z_FREE_LEVEL:
            raise Exception('Syringe is too low!!!')

        # check syringe is empty first
        if not self.syringe.is_empty():
            raise Exception('Syringe is not empty!!! so probably not clear')

        # move syringe into tube
        self.xy_axis.move_to(XY_ABOVE_TUBE)
        self.z_axis.move_to(Z_SYRINGE_IN_OIL)

        self.syringe.pump(self.oil_volume_to_pump)
        self.syringe.deliver(SYRINGE_BUFFER_VOLUME)  # we drop one buffer to make the plunger ready, there is some backslash so by going down a bit we remove such issue

        # move up
        self.z_axis.move_to(Z_FREE_LEVEL)

        # go to petri dish to be ready to make droplets
        self.xy_axis.move_to(XY_ABOVE_DISH)
        self.z_axis.move_to(Z_ABOVE_SURFACTANT)

    def make_droplets(self):
        # make all droplets
        for droplet_info in self.droplet_list:
            self.deliver_droplet(droplet_info)
        self.z_axis.move_to(Z_FREE_LEVEL)


    def is_ready_to_make_droplet(self):

        TOLERANCE = 1  # mm

        def is_with_in(value, reference_value, with_in_value):
            min_bound = reference_value - with_in_value
            max_bound = reference_value + with_in_value
            return min_bound <= value <= max_bound

        current_xy = self.xy_axis.get_current_position()
        current_x = current_xy[0]
        current_y = current_xy[1]
        current_z = self.z_axis.get_current_position()

        target_x = XY_ABOVE_DISH[0]
        target_y = XY_ABOVE_DISH[1]
        target_z = Z_ABOVE_SURFACTANT

        x_ok = is_with_in(current_x, target_x, TOLERANCE)
        y_ok = is_with_in(current_y, target_y, TOLERANCE)
        z_ok = is_with_in(current_z, target_z, TOLERANCE)

        return x_ok and y_ok and z_ok


    def deliver_droplet(self, droplet_info):
        # this function can only start if we are in the correct position, this step is really sensible and starting it from a bad position is likelly to break something
        if not self.is_ready_to_make_droplet():
            raise Exception('Deliver droplet can only start if we are in the correct position, this step is really sensible and starting it from a bad position is likelly to break something')

        volume = droplet_info['volume']
        relative_position = droplet_info['position']

        # if relative position is valid
        if self.is_droplet_position_valid(relative_position):

            # move relative
            self.xy_axis.move(relative_position)

            # deliver
            self.z_axis.move_to(Z_AT_SURFACTANT)
            self.syringe.deliver(volume)
            self.z_axis.move_to(Z_ABOVE_SURFACTANT)

            # come back
            self.xy_axis.move_to(XY_ABOVE_DISH)

        else:
            print 'Skipping droplet at position {}, not valid position'
