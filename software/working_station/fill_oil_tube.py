import os
import numpy as np

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

##
from tools.tasks import Task

from constants import TUBE_OIL_VOLUME
from constants import OIL_PUMP_CHEMICALS

INLET = 'I'
OUTLET = 'O'

FILL_HEAD_DIPENSE_LEVEL = 30
FILL_HEAD_CONTACT_LEVEL = 38


def proba_normalize(x):
    x = np.array(x, dtype=float)
    if np.sum(x) == 0:
        x = np.ones(x.shape)
    return x / np.sum(x, dtype=float)


class FillOilTube(Task):

    def __init__(self, pump_controller, fill_head):
        Task.__init__(self)
        self.pump_controller = pump_controller
        self.fill_head = fill_head
        self.start()

    def main(self):

        if 'oil_formulation' in self.XP_dict:

            # get the field of interest
            oil_formulation = self.XP_dict['oil_formulation']

            # check oils are loaded on the machine
            for oil_name in oil_formulation.keys():
                if oil_name not in OIL_PUMP_CHEMICALS.values():
                    raise Exception('{} is not loaded in the any of the oil pumps'.format(oil_name))

            # normalize ratios and compute oil volumes
            normalized_values = proba_normalize(oil_formulation.values())
            oil_volumes = normalized_values * TUBE_OIL_VOLUME

            # make sure ready
            self.fill_head.home()
            self.pump_controller.apply_command_to_pumps(oil_formulation.keys(), 'wait_until_idle')

            # go to dipesning level
            self.fill_head.move_to(FILL_HEAD_DIPENSE_LEVEL, wait=False)

            # pump
            for i, oil_name in enumerate(oil_formulation.keys()):
                pump_name = OIL_PUMP_CHEMICALS.keys()[OIL_PUMP_CHEMICALS.values().index(oil_name)]
                pump = self.pump_controller.pumps[pump_name]
                volume_in_ml = oil_volumes[i]

                pump.pump(volume_in_ml, from_valve=INLET)

            # wait
            self.pump_controller.apply_command_to_pumps(oil_formulation.keys(), 'wait_until_idle')
            self.fill_head.wait_until_idle()
            if self.fill_head.get_switch_state():
                raise Exception('Fill head oil mixture did not go down, stepper might be broken...')

            # pump
            for i, oil_name in enumerate(oil_formulation.keys()):
                pump_name = OIL_PUMP_CHEMICALS.keys()[OIL_PUMP_CHEMICALS.values().index(oil_name)]
                pump = self.pump_controller.pumps[pump_name]
                volume_in_ml = oil_volumes[i]

                pump.deliver(volume_in_ml, to_valve=OUTLET)

            # wait
            self.pump_controller.apply_command_to_pumps(oil_formulation.keys(), 'wait_until_idle')

            # move down to make contact and remove the remaining pending drops
            self.fill_head.move_to(FILL_HEAD_CONTACT_LEVEL)
            # go up home
            self.fill_head.home()
