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
HOMING_EVERY_N_XP = 1
MANAGER_STORAGE_FILE = os.path.join(HERE_PATH, 'manager_storage.json')
MAX_WASTE_VOLUME = 10000  # 10L in ml


def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)


def read_XP_from_file(filename):
    with open(filename) as f:
        return json.load(f)


class XPManager(threading.Thread):

    def __init__(self, robot, working_station_dict, verbose=True):
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
        self.verbose = verbose
        self._n_xp_with_droplet_done = 0

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

    def create_default_manager_storage_file(self):
        manager_storage = {}
        manager_storage['waste_volume'] = MAX_WASTE_VOLUME
        self.save_manager_storage(manager_storage)
        if self.verbose:
            print '-----WARNING-----'
            print 'Created default manager storage file at {}'.format(MANAGER_STORAGE_FILE)
            print manager_storage

    def get_manager_storage(self):
        if not os.path.exists(MANAGER_STORAGE_FILE):
            self.create_default_manager_storage_file()
        return read_XP_from_file(MANAGER_STORAGE_FILE)

    def save_manager_storage(self, manager_storage_dict):
        save_to_json(manager_storage_dict, MANAGER_STORAGE_FILE)

    def get_waste_volume(self):
        manager_storage = self.get_manager_storage()
        return manager_storage['waste_volume']

    def set_waste_volume(self, volume_in_ml):
        manager_storage = self.get_manager_storage()
        manager_storage['waste_volume'] = volume_in_ml
        self.save_manager_storage(manager_storage)

    def add_waste_volume(self, volume_in_ml):
        current_waste_volume = self.get_waste_volume()
        self.set_waste_volume(current_waste_volume + volume_in_ml)

    def check_waste_volume(self):
        current_waste_volume = self.get_waste_volume()
        if self.verbose:
            print 'Current waste volume is {} mL'.format(current_waste_volume)
        if  current_waste_volume >= MAX_WASTE_VOLUME:
            print '-----WARNING-----'
            print 'Waste seems to be full!, option are:'
            print '1- The waste is really full, change it, update new volume to zero'
            print '2- The waste is not full, update new volume'
            user_input_validated = False
            while not user_input_validated:
                response = raw_input('Enter the new volume in mL, 0 if empty: ')
                if response.isdigit():
                    new_waste_volume_in_ml = int(response)
                    if 0 <= new_waste_volume_in_ml <= MAX_WASTE_VOLUME:
                        self.set_waste_volume(new_waste_volume_in_ml)
                        user_input_validated = True
                    else:
                        print 'New volume must be >=0 and <={}'.format(MAX_WASTE_VOLUME)
                else:
                    print '{} is not a valid number, you must provide a positive int or 0'.format(response)
            print 'Great! manager continue is routine with waste volume = {}'.format(self.get_waste_volume())
            print '-----------------'

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

        self.check_waste_volume()

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

        # variable for checking what needs to be cleaned
        clean_tube = False
        clean_syringe = False
        clean_oil_waste_volume = 0
        clean_dish_waste_volume = 0

        # check if any droplet to be made, thus syringe cleaned
        station_id = 2
        droplet_XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if droplet_XP_dict is not None:
            self.working_station_dict['make_droplet_station'].load_XP(droplet_XP_dict)
            if 'droplets' in droplet_XP_dict:
                if len(droplet_XP_dict['droplets']) > 0:
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
                if len(XP_dict['droplets']) > 0:
                    clean_syringe = True
            if 'force_clean_syringe' in XP_dict:
                if XP_dict['force_clean_syringe'] is True:
                    clean_syringe = True

        # launch station 4, cleaning
        station_id = 4
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.working_station_dict['clean_dish_station'].launch(XP_dict)
            clean_dish_waste_volume = self.working_station_dict['clean_dish_station'].get_added_waste_volume()
            clean_tube = True

        self.working_station_dict['clean_oil_station'].launch(XP_dict, clean_tube=clean_tube, clean_syringe=clean_syringe)  # only clean tube or syringe if needed. They share a pump so are combined in one working station with condition. XP_dict does not matter
        clean_oil_waste_volume = self.working_station_dict['clean_oil_station'].get_added_waste_volume()


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

        # update the waste counter
        self.add_waste_volume(clean_oil_waste_volume + clean_dish_waste_volume)

        # if there was an XP at station 7, the last one, save and print XP info
        station_id = 7
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.add_end_info_to_XP_dict(XP_dict)
            self.save_run_info(XP_dict)

            if self.verbose:
                if 'manager_info' in XP_dict:
                    print 'XP started at {}, ended at {}, lasted {} seconds'.format( XP_dict['manager_info']['start_ctime'], XP_dict['manager_info']['end_ctime'], XP_dict['manager_info']['duration'])

        # this is the moment to pause all station finished and before placing new droplets
        self.apply_pause()

        # before placing new droplet, we home again the robot in case of slight shift on execution
        if self._n_xp_with_droplet_done > HOMING_EVERY_N_XP:
            self.robot.init(user_query=False)
            self._n_xp_with_droplet_done = 0

        # launch station 2, make droplets
        if droplet_XP_dict is not None:
            if 'droplets' in droplet_XP_dict:
                if len(droplet_XP_dict['droplets']) > 0:
                    self._n_xp_with_droplet_done += 1
            self.working_station_dict['make_droplet_station'].make_droplets()  # this is a blocking call
