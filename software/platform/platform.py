from commanduino import CommandManager
from commanduino.devices.axis import Axis, MultiAxis

import logging
logging.basicConfig(level=logging.INFO)

cmdMng = CommandManager.from_configfile('./platform_config.json')
