import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

from tools.tasks import Task

INLET = 'E'
OUTLET = 'O'


class FillPetriDish(Task):

    def __init__(self, surfactant_pump):
        Task.__init__(self)
        self.surfactant_pump = surfactant_pump
        self.start()

    def main(self):
        self.surfactant_pump.transfer(
            self.XP_dict['surfactant_volume'],
            from_valve=INLET,
            to_valve=OUTLET)
