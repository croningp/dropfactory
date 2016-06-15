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
import json
import threading

from constants import N_POSITION

from xp_queue import XPQueue

SLEEP_TIME = 0.1


def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)


class XPManager(threading.Thread):

    def __init__(self, robot, working_station_dict):
        """
        The robot, pumps and working station must be initalized already
        working_station_dict contain all the instance of the useful station, that is, with exact name:
        - fill_dish_station
        - fill_oil_station
        - clean_dish_station
        - clean_oil_station
        - make_droplet_station
        - record_video_station
        - wait_station
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.xp_queue = XPQueue(N_POSITION)
        self.robot = robot
        self.working_station_dict = working_station_dict

        self.is_paused = False
        self.verbose = True

        self.start()

    def add_XP(self, XP_dict):
        self.xp_queue.add_XP(XP_dict)

    def remove_XP(self, XP_dict):
        self.xp_queue.remove_XP(XP_dict)

    def empty_XP_queue(self):
        self.xp_queue.empty_XP_waiting()

    def count_XP_ongoing(self):
        return self.xp_queue.count_XP_ongoing()

    def count_XP_waiting(self):
        return self.xp_queue.count_XP_waiting()

    def wait_until_XP_finished(self):
        while self.xp_queue.any_XP_ongoing() or self.xp_queue.any_XP_waiting():
            time.sleep(SLEEP_TIME)

    def run(self):
        self.interrupted.acquire()
        while self.interrupted.locked():
            if self.xp_queue.any_XP_ongoing():
                self.handle_XP_ongoing()
                self.robot.rotate_geneva_wheels()
            else:
                self.apply_pause()
            self.xp_queue.cycle()
            time.sleep(SLEEP_TIME)

    def stop(self):
        self.interrupted.release()

    def pause(self):
        self.is_paused = True

    def unpause(self):
        self.is_paused = False

    def apply_pause(self):
        if self.is_paused and self.verbose:
            print 'Manager paused...'
        while self.is_paused:
            time.sleep(SLEEP_TIME)
        if self.is_paused and self.verbose:
            print 'Manager running again'

    def add_start_info_to_XP_dict(self, XP_dict):
        time_now = time.time()
        XP_dict['manager_info'] = {}
        XP_dict['manager_info']['start_time'] = time_now
        XP_dict['manager_info']['start_ctime'] = time.ctime(time_now)

    def add_end_info_to_XP_dict(self, XP_dict):
        start_time = XP_dict['manager_info']['start_time']

        end_time = time.time()
        XP_dict['manager_info']['end_time'] = end_time
        XP_dict['manager_info']['end_ctime'] = time.ctime(end_time)

        XP_dict['manager_info']['duration'] = end_time - start_time

    def save_run_info(self, XP_dict):
        if 'run_info' in XP_dict:
            filename = XP_dict['run_info']['filename']
            data = XP_dict['manager_info']
            save_to_json(data, filename)

    def handle_XP_ongoing(self):

        if self.verbose:
            print '###\n{} XP ongoing and {} XP waiting'.format(self.count_XP_ongoing(), self.count_XP_waiting())

        # station 1, 5, 6, and 7 are doing nothing just waiting for min_waiting_time
        # fin max waiting time
        max_min_waiting_time = 0
        for station_id in [1, 5, 6, 7]:
            XP_dict = self.xp_queue.get_XP_ongoing(station_id)
            if XP_dict is not None:
                if 'min_waiting_time' in XP_dict:
                    min_waiting_time = XP_dict['min_waiting_time']
                    if min_waiting_time > max_min_waiting_time:
                        max_min_waiting_time = min_waiting_time

        waiting_XP_dict = {'min_waiting_time': max_min_waiting_time}
        self.working_station_dict['wait_station'].launch(waiting_XP_dict)

        # variable for checking what need to be cleaned
        clean_tube = False
        clean_syringe = False

        # check if any droplet to be made, thus syringe cleaned
        station_id = 2
        droplet_XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if droplet_XP_dict is not None:
            self.working_station_dict['make_droplet_station'].load_XP(droplet_XP_dict)
            if 'droplets' in droplet_XP_dict:
                if droplet_XP_dict['droplets'] > 0:
                    clean_syringe = True

        # launch station 0, filling step and record time of start
        station_id = 0
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.add_start_info_to_XP_dict(XP_dict)
            self.working_station_dict['fill_oil_station'].launch(XP_dict)
            self.working_station_dict['fill_dish_station'].launch(XP_dict)

        # launch station 3, recording video
        # also check if droplet was just made before, hence is step 3 filming
        station_id = 3
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.working_station_dict['record_video_station'].launch(XP_dict)
            if 'droplets' in XP_dict:
                if XP_dict['droplets'] > 0:
                    clean_syringe = True

        # launch station 4, cleaning
        station_id = 4
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.working_station_dict['clean_dish_station'].launch(XP_dict)
            clean_tube = True

        self.working_station_dict['clean_oil_station'].launch(XP_dict, clean_tube=clean_tube, clean_syringe=clean_syringe)  # only clean tube or syringe if needed. They share a pump so are combined in one working station with condition. XP_dict does not matter

        # launch station 2, prepare droplets only once syringe is cleaned
        if droplet_XP_dict is not None:
            self.working_station_dict['clean_oil_station'].wait_until_idle()
            self.working_station_dict['make_droplet_station'].start_filling_syringe_step()

        # wait for all to finish
        self.working_station_dict['wait_station'].wait_until_idle()
        self.working_station_dict['clean_oil_station'].wait_until_idle()
        self.working_station_dict['clean_dish_station'].wait_until_idle()
        self.working_station_dict['fill_oil_station'].wait_until_idle()
        self.working_station_dict['fill_dish_station'].wait_until_idle()
        self.working_station_dict['make_droplet_station'].wait_until_idle()
        self.working_station_dict['record_video_station'].wait_until_idle()

        # if there was an XP at station 7, the last one, record it
        station_id = 7
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.add_end_info_to_XP_dict(XP_dict)
            self.save_run_info(XP_dict)

            if self.verbose:
                if 'manager_info' in XP_dict:
                    print 'XP started on {}, ended at {}, lasted {} seconds'.format( XP_dict['manager_info']['start_ctime'], XP_dict['manager_info']['end_ctime'], XP_dict['manager_info']['duration'])

        # this is the moment to pause all station finished and before placing new droplets
        self.apply_pause()

        # launch station 2, make droplets
        if droplet_XP_dict is not None:
            self.working_station_dict['make_droplet_station'].make_droplets()  # this is a blocking call
