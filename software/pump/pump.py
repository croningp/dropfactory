import os
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

from pycont.controller import MultiPumpController

configfile = os.path.join(HERE_PATH, 'pump_config.json')
controller = MultiPumpController.from_configfile(configfile)
