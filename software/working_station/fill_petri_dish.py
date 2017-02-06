import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

from tools.tasks import Task

from constants import MAX_SURFACTANT_VOLUME
from constants import SURFACTANT_PUMP_CHEMICALS

INLET = 'E'
OUTLET = 'O'


def proba_normalize(x):
    x = np.array(x, dtype=float)
    if np.sum(x) == 0:
        x = np.ones(x.shape)
    return x / np.sum(x, dtype=float)


class FillPetriDish(Task):

    def __init__(self, surfactant_pump):
        Task.__init__(self)
        self.surfactant_pump = surfactant_pump
        self.start()

    def main(self):

        if 'surfactant_formulation' in self.XP_dict:
            if 'surfactant_volume' in self.XP_dict:
                # get the fields of interest
                surfactant_volume = self.XP_dict['surfactant_volume']
                if surfactant_volume > MAX_SURFACTANT_VOLUME:
                    raise Exception('Surfactant volume of {} is above the max of {}').format(surfactant_volume, MAX_SURFACTANT_VOLUME)

                surfactant_formulation = self.XP_dict['surfactant_formulation']

                # check surfactants are loaded on the machine
                for surfactant_name in surfactant_formulation.keys():
                    if surfactant_name not in SURFACTANT_PUMP_CHEMICALS.values():
                        raise Exception('{} is not loaded in the any of the surfactant pumps'.format(surfactant_name))

                # normalize ratios and compute surfactant volumes
                normalized_values = proba_normalize(surfactant_formulation.values())
                surfactant_volumes = normalized_values * surfactant_volume

                # wait pumps ready
                self.pump_controller.apply_command_to_pumps(SURFACTANT_PUMP_CHEMICALS.keys(), 'wait_until_idle')

                # pump
                for i, surfactant_name in enumerate(surfactant_formulation.keys()):
                    pump_name = SURFACTANT_PUMP_CHEMICALS.keys()[SURFACTANT_PUMP_CHEMICALS.values().index(surfactant_name)]
                    pump = self.pump_controller.pumps[pump_name]
                    volume_in_ml = surfactant_volumes[i]

                    pump.pump(volume_in_ml, from_valve=INLET)

                # wait
                self.pump_controller.apply_command_to_pumps(SURFACTANT_PUMP_CHEMICALS.keys(), 'wait_until_idle')

                # deliver
                for i, surfactant_name in enumerate(surfactant_formulation.keys()):
                    pump_name = SURFACTANT_PUMP_CHEMICALS.keys()[SURFACTANT_PUMP_CHEMICALS.values().index(surfactant_name)]
                    pump = self.pump_controller.pumps[pump_name]
                    volume_in_ml = surfactant_volumes[i]

                    pump.deliver(volume_in_ml, to_valve=OUTLET)

                # wait
                self.pump_controller.apply_command_to_pumps(SURFACTANT_PUMP_CHEMICALS.keys(), 'wait_until_idle')


            else:
                raise Exception('No surfactant volume specified!')
