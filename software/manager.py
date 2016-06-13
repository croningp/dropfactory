import os

# this get our current location in the file system
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# adding parent directory to path, so we can access the utils easily
import sys
sys.path.append(HERE_PATH)

import logging
logging.basicConfig(level=logging.INFO)

##
from pump import pump
if not pump.controller.are_pumps_initialized():
    raise Exception('Pumps not initalized, run initialize.py script first')

from robot import robot
robot.init()


# load station
working_station_dict = {}
from working_station.fill_petri_dish import FillPetriDish
working_station_dict['fill_dish_station'] = FillPetriDish(pump.controller.surfactant)

from working_station.fill_oil_tube import FillOilTube
working_station_dict['fill_oil_station'] = FillOilTube(pump.controller, robot.FILL_HEAD_MIXTURE)

from working_station.clean_petri_dish import CleanPetriDish
working_station_dict['clean_dish_station'] = CleanPetriDish(robot.CLEAN_HEAD_DISH,
                                                            robot.CLEAN_HEAD_DISH_SWITCH,
                                                            pump.controller.waste_dish,
                                                            pump.controller.water_dish,
                                                            pump.controller.acetone_dish)


from working_station.clean_oil_parts import CleanOilParts
working_station_dict['clean_oil_station'] = CleanOilParts(robot.XY,
                                                          robot.Z,
                                                          robot.SYRINGE,
                                                          robot.CLEAN_HEAD_MIXTURE,
                                                          pump.controller.waste_oil,
                                                          pump.controller.acetone_oil)

from working_station.make_droplets import MakeDroplets
working_station_dict['make_droplet_station'] = MakeDroplets(robot.XY, robot.Z, robot.SYRINGE)

from working_station.record_video import RecordVideo
working_station_dict['record_video_station'] = RecordVideo()

#
from tools.xp_manager import XPManager
manager = XPManager(robot, working_station_dict)
