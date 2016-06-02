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
from working_station.fill_petri_dish import FillPetriDish
fill_dish_station = FillPetriDish(pump.controller.surfactant)

from working_station.fill_oil_tube import FillOilTube
fill_oil_station = FillOilTube(pump.controller)

from working_station.clean_petri_dish import CleanPetriDish
clean_dish_station = CleanPetriDish(robot.CLEAN_HEAD_DISH,
                                    pump.controller.waste_dish,
                                    pump.controller.water_dish,
                                    pump.controller.acetone_dish)


from working_station.clean_oil_parts import CleanOilParts
clean_oils_station = CleanOilParts(robot.XY,
                                   robot.Z,
                                   robot.SYRINGE,
                                   robot.CLEAN_HEAD_MIXTURE,
                                   pump.controller.waste_oil,
                                   pump.controller.acetone_oil)

from working_station.make_droplets import MakeDroplets
make_droplet_station = MakeDroplets(robot.XY, robot.Z, robot.SYRINGE)

from working_station.record_video import RecordVideo
record_video_station = RecordVideo()

#
