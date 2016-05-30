from pycont.controller import MultiPumpController

import logging
logging.basicConfig(level=logging.INFO)

controller = MultiPumpController.from_configfile('./pump_config.json')
