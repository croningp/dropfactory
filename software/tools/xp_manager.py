import os
import inspect
HERE_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

import logging
logging.basicConfig(level=logging.INFO)

# adding parent directory to path, so we can access the utils easily
import sys
root_path = os.path.join(HERE_PATH, '..')
sys.path.append(root_path)

import time
import threading

from constants import N_POSITION

from xp_queue import XPQueue

SLEEP_TIME = 0.1


class XPManager(threading.Thread):

    def __init__(self, robot, working_station_dict):
        """
        The robot, pumps and working station must be initalized already
        working_station_dict contain all the instance of the useful station, that is, with exact name:
        - fill_dish_station
        - fill_oil_station
        - clean_dish_station
        - clean_oils_station
        - make_droplet_station
        - record_video_station
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.xp_queue = XPQueue(N_POSITION)
        self.robot = robot
        self.working_station_dict = working_station_dict

    def add_XP(self, XP_dict):
        self.xp_queue.add_XP(XP_dict)

    def remove_XP(self, XP_dict):
        self.xp_queue.remove_XP(XP_dict)

    def empty_XP_queue(self):
        self.xp_queue.empty_XP_waiting()

    def run(self):
        self.interrupted.acquire()
        while self.interrupted.locked():
            if self.xp_queue.any_XP_ongoing():
                self.handle_XP_ongoing()
                self.robot.rotate_geneva_wheels()
            self.xp_queue.cycle()
            time.sleep(SLEEP_TIME)

    def stop(self):
        self.interrupted.release()

    def handle_XP_ongoing(self):

        # station 1, 5, 6, 7 are doing nothing

        # check if any droplet to be made, thus syringe cleaned
        clean_syringe = False

        station_id = 2
        droplet_XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if droplet_XP_dict is not None:
            self.working_station_dict['make_droplet_station'].load_XP(droplet_XP_dict)
            clean_syringe = True

        # launch station 0, filling step
        station_id = 0
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.working_station_dict['fill_oil_station'].launch(XP_dict)
            self.working_station_dict['fill_dish_station'].launch(XP_dict)

        # launch station 3, recording video
        station_id = 3
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.working_station_dict['record_video_station'].launch(XP_dict)

        # launch station 4, cleaning
        station_id = 4
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.working_station_dict['clean_oils_station'].launch(XP_dict, clean_syringe=clean_syringe)  # only clean syringe if needed, i.e. if droplets to be made
            self.working_station_dict['clean_dish_station'].launch(XP_dict)

        # launch station 2, prepare droplets only once syringe is cleaned
        if droplet_XP_dict is not None:
            self.working_station_dict['clean_oils_station'].wait_until_idle()
            self.working_station_dict['make_droplet_station'].start_filling_syringe_step()

        # wait for all to finish
        self.working_station_dict['clean_dish_station'].wait_until_idle()
        self.working_station_dict['fill_oil_station'].wait_until_idle()
        self.working_station_dict['fill_dish_station'].wait_until_idle()
        self.working_station_dict['make_droplet_station'].wait_until_idle()
        self.working_station_dict['record_video_station'].wait_until_idle()

        # launch station 2, make droplets
        if droplet_XP_dict is not None:
            self.working_station_dict['make_droplet_station'].make_droplets()  # this is a blocking call
