import os
import numpy as np

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

from tools.tasks import Task

INLETS = {
    'dep': 'E',
    'octanoic': 'E',
    'octanol': 'I',
    'pentanol': 'I'
}

OUTLETS = {
    'dep': 'O',
    'octanoic': 'O',
    'octanol': 'O',
    'pentanol': 'O'
}

TUBE_VOLUME = 0.5  # mL


def proba_normalize(x):
    x = np.array(x, dtype=float)
    if np.sum(x) == 0:
        x = np.ones(x.shape)
    return x / np.sum(x, dtype=float)


class FillOilTube(Task):

    def __init__(self, pump_controller):
        Task.__init__(self)
        self.pump_controller = pump_controller
        self.start()

    def main(self):

        # get the field of interest
        formulation = self.XP_dict['formulation']

        # normallize ratios and compute oil volumes
        normalized_values = proba_normalize(formulation.values())
        oil_volumes = normalized_values * TUBE_VOLUME

        # wait
        self.pump_controller.apply_command_to_pumps(formulation.keys(), 'wait_until_idle')

        # pump
        for i in range(len(formulation)):
            pump_name = formulation.keys()[i]
            pump = self.pump_controller.pumps[pump_name]
            volume_in_ml = oil_volumes[i]
            inlet = INLETS[pump_name]

            pump.pump(volume_in_ml, inlet)

        # wait
        self.pump_controller.apply_command_to_pumps(formulation.keys(), 'wait_until_idle')

        # deliver
        for i in range(len(formulation)):
            pump_name = formulation.keys()[i]
            pump = self.pump_controller.pumps[pump_name]
            volume_in_ml = oil_volumes[i]
            outlet = OUTLETS[pump_name]

            pump.deliver(volume_in_ml, outlet)

        # wait
        self.pump_controller.apply_command_to_pumps(formulation.keys(), 'wait_until_idle')
