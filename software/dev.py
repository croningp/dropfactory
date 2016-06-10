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


##
from working_station.fill_petri_dish import FillPetriDish
from working_station.clean_petri_dish import CleanPetriDish
from working_station.clean_oil_parts import CleanOilParts
from working_station.fill_oil_tube import FillOilTube
from working_station.record_video import RecordVideo
from working_station.make_droplets import MakeDroplets


import time


XP_dict = {
    'surfactant_volume': 3.5,
    'formulation': {
        'octanol': 0,
        'octanoic': 0,
        'pentanol': 1,
        'dep': 0
    },
    'video_info': {
        'path': os.path.join(HERE_PATH, 'video.avi'),
        'duration': 10
    },
    'droplets': [
        {
            'volume': 2,
            'position': [0, 0]
        },
        {
            'volume': 4,
            'position': [10, 0]
        }
    ]
}


fill_dish_station = FillPetriDish(pump.controller.surfactant)

fill_oil_station = FillOilTube(pump.controller, robot.FILL_HEAD_MIXTURE)

clean_dish_station = CleanPetriDish(robot.CLEAN_HEAD_DISH,
                                    pump.controller.waste_dish,
                                    pump.controller.water_dish,
                                    pump.controller.acetone_dish)

clean_oil_station = CleanOilParts(robot.XY, robot.Z, robot.SYRINGE, robot.CLEAN_HEAD_MIXTURE, pump.controller.waste_oil, pump.controller.acetone_oil)

make_droplet_station = MakeDroplets(robot.XY, robot.Z, robot.SYRINGE)

record_video_station = RecordVideo()
