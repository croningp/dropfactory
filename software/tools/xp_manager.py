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
import tempfile
import threading
import subprocess

from tools import email_notification
from tools.watchdog import Watchdog
from constants import N_POSITION
from constants import OIL_PUMP_CHEMICALS
from constants import SURFACTANT_PUMP_CHEMICALS
from constants import ARENA_TYPE

from xp_queue import XPQueue

SLEEP_TIME = 0.1
HOMING_EVERY_N_XP = 30
MANAGER_STORAGE_FILE = os.path.join(HERE_PATH, 'manager_storage.json')
MAX_WASTE_VOLUME = 10000  # 10L in ml
WASTE_CORRECTION = 0.9  # waste correction
TIMEOUT_WASTE = 300

EMAILS_TO_NOTIFY = ['jonathan.grizou@glasgow.ac.uk', 'l.points.1@research.gla.ac.uk']  # must be a list

WATCHDOG_TIMEOUT = 600


def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)


def read_XP_from_file(filename):
    with open(filename) as f:
        return json.load(f)


def send_email_notification(subject, body):
    for toaddr in EMAILS_TO_NOTIFY:
        email_notification.send_email_notification(toaddr, subject, body)


def send_watchdog_email():
    send_email_notification('[Dropfactory] Watchdog timout', 'Watchdog raised, something might be wrong with dropfactory')


def timeout_editor_input(timeout=20, sleep_time=0.1, editor='gedit'):
    # generate tmp file
    tmpwastefilename = tempfile.NamedTemporaryFile().name

    # open a gedit file
    proc = subprocess.Popen([editor, tmpwastefilename])

    # Wait until process terminates
    start_time = time.time()
    elapsed = 0
    while elapsed <  timeout:
        if proc.poll() is not None:
            if os.path.exists(tmpwastefilename):
                with open(tmpwastefilename) as f:
                    return f.readline().strip()
            else:
                return ''
        time.sleep(sleep_time)
        elapsed = time.time() - start_time
        time.sleep(sleep_time)
    proc.terminate()
    return ''


class XPManager(threading.Thread):

    def __init__(self, pump, robot, working_station_dict, verbose=True):
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
        self.pump = pump
        self.robot = robot
        self.working_station_dict = working_station_dict

        self.is_paused = False
        self.verbose = verbose
        self._n_xp_with_droplet_done = 0
        self.bypass_waste_security = False

        self.start()

    def add_XP(self, XP_dict):
        if self.check_XP_valid(XP_dict):
            self.xp_queue.add_XP(XP_dict)
        else:
            print 'XP is not valid and will not be run on the platform, see messages above'

    def check_XP_valid(self, XP_dict):
        # check oils
        if 'oil_formulation' in XP_dict:
            oil_formulation = XP_dict['oil_formulation']
            for oil_name in oil_formulation.keys():
                if oil_name not in OIL_PUMP_CHEMICALS.values():
                    print '{} is not loaded in the any of the oil pumps'.format(oil_name)
                    return False
        # check surfactants
        if 'surfactant_formulation' in XP_dict:
            surfactant_formulation = XP_dict['surfactant_formulation']
            for surfactant_name in surfactant_formulation.keys():
                if surfactant_name not in SURFACTANT_PUMP_CHEMICALS.values():
                    print '{} is not loaded in the any of the surfactant pumps'.format(surfactant_name)
                    return False
        # check arena
        if 'arena_type' in XP_dict:
            arena_type = XP_dict['arena_type']
            if arena_type != ARENA_TYPE:
                print '{} arenas are not loaded on dropfactory'.format(arena_type)
                return False
        #
        return True

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
        self.watchdog = Watchdog(WATCHDOG_TIMEOUT, send_watchdog_email)
        while self.interrupted.locked():
            if self.xp_queue.any_XP_ongoing():
                self.handle_XP_ongoing()
                self.robot.rotate_geneva_wheels()
                # ping the watchdog here so we get a message when no more experiments are running
                self.watchdog.reset()  # we do a reset here because watchdog can be raised for reasons other than a bug/exception/no more XP, e.g. when the waste is full or manager is paused
            else:
                # a pause is done inside the handle_XP_ongoing main, but if there is not XP ongoing, it is still useful to be able to pause
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
        if self.verbose:
            print 'Adding {} mL to waste'.format(volume_in_ml)
        current_waste_volume = self.get_waste_volume()
        self.set_waste_volume(current_waste_volume + volume_in_ml)

    def check_waste_volume(self):
        current_waste_volume = self.get_waste_volume()
        if self.verbose:
            print 'Current waste volume is {} mL'.format(current_waste_volume)
        if current_waste_volume >= MAX_WASTE_VOLUME:
            send_email_notification('[Dropfactory] Waste is full', 'Waste seems to be full, go change it.')
            print '-----WARNING-----'
            print 'Waste seems to be full!, option are:'
            print '1- The waste is really full, change it, update new volume to zero'
            print '2- The waste is not full, update new volume'
            user_input_validated = False
            while not user_input_validated:
                if self.bypass_waste_security:
                    print 'Warning: Bypassing waste security!'
                    user_input_validated = True
                else:
                    print 'Enter the new volume in mL on the first line of the open file, save and quit, put 0 if empty (timeout {}sec): '.format(TIMEOUT_WASTE)
                    response = timeout_editor_input(TIMEOUT_WASTE)
                    if response.isdigit():
                        new_waste_volume_in_ml = int(response)
                        if 0 <= new_waste_volume_in_ml <= MAX_WASTE_VOLUME:
                            self.set_waste_volume(new_waste_volume_in_ml)
                            user_input_validated = True
                        else:
                            print 'New volume must be >=0 and <={}'.format(MAX_WASTE_VOLUME)
                    else:
                        print '{} is not a valid number, you must provide a positive int or 0'.format(response)
            print 'Great! manager continue his routine with waste volume = {}'.format(self.get_waste_volume())
            print '-----------------'

    def add_start_info_to_XP_dict(self, XP_dict):
        time_now = time.time()
        XP_dict['manager_info'] = {}
        XP_dict['manager_info']['start_time'] = time_now
        XP_dict['manager_info']['start_ctime'] = time.ctime(time_now)


    def add_temperature_info_to_XP_dict(self, XP_dict):
        XP_dict['manager_info']['temperature'] = self.robot.TEMPERATURE_SENSOR.get_celsius()
        XP_dict['manager_info']['humidity'] = self.robot.TEMPERATURE_SENSOR.get_humidity()
        temp_time = time.time()
        XP_dict['manager_info']['temp_time'] = temp_time
        XP_dict['manager_info']['temp_ctime'] = time.ctime(temp_time)

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

        start_time = time.time()

        if self.verbose:
            print '###\n{} XP ongoing and {} XP waiting'.format(self.count_XP_ongoing(), self.count_XP_waiting())

        # variable for checking what needs to be cleaned
        clean_tube = False
        clean_syringe = False
        clean_oil_waste_volume = 0
        clean_dish_waste_volume = 0

        # launch station 3 (recording video) before all else, we home from time to time and this delays the start of the other station
        # also check if droplet was just made before, hence is step 3 filming
        station_id = 3
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.working_station_dict['record_video_station'].launch(XP_dict)
            if 'droplets' in XP_dict:
                if len(XP_dict['droplets']) > 0:
                    clean_syringe = True

        # before starting and every HOMING_EVERY_N_XP, we home again the robot in case of slight shift on execution
        if self._n_xp_with_droplet_done >= HOMING_EVERY_N_XP:
            if self.verbose:
                print 'Robot homing..'
            self.robot.init(user_query=False, init_syringe=True, init_syringe_above_vial=True, init_geneva_wheel=False)
            self._n_xp_with_droplet_done = 0

        # station 5, 6, and 7 are doing nothing just waiting for min_waiting_time for evaporation
        # find max waiting time
        max_min_waiting_time = 0
        for station_id in [5, 6, 7]:
            XP_dict = self.xp_queue.get_XP_ongoing(station_id)
            if XP_dict is not None:
                if 'min_waiting_time' in XP_dict:
                    min_waiting_time = XP_dict['min_waiting_time']
                    if min_waiting_time > max_min_waiting_time:
                        max_min_waiting_time = min_waiting_time
        # apply max min waiting time
        waiting_XP_dict = {'min_waiting_time': max_min_waiting_time}
        self.working_station_dict['wait_station'].launch(waiting_XP_dict)

        # check if any droplet to be made, thus syringe cleaned
        station_id = 2
        droplet_XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if droplet_XP_dict is not None:
            self.working_station_dict['make_droplet_station'].load_XP(droplet_XP_dict)
            if 'droplets' in droplet_XP_dict:
                if len(droplet_XP_dict['droplets']) > 0:
                    clean_syringe = True
            if 'force_clean_syringe' in droplet_XP_dict:
                if droplet_XP_dict['force_clean_syringe'] is True:
                    clean_syringe = True

        # launch station 0, filling step and record time of start
        station_id = 0
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.add_start_info_to_XP_dict(XP_dict)
            self.working_station_dict['fill_oil_station'].launch(XP_dict)
            self.working_station_dict['fill_dish_station'].launch(XP_dict)

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

        # check time to execute all stations
        if self.verbose:
            elapsed = time.time() - start_time
            print 'Running all station before droplet placing took {} seconds'.format(round(elapsed, 2))

        # update the waste counter
        to_add_waste_volume = clean_oil_waste_volume + clean_dish_waste_volume
        self.add_waste_volume(WASTE_CORRECTION * to_add_waste_volume)
        self.check_waste_volume()

        # if there was an XP at station 7, the last one, save and print XP info
        station_id = 7
        XP_dict = self.xp_queue.get_XP_ongoing(station_id)
        if XP_dict is not None:
            self.add_end_info_to_XP_dict(XP_dict)
            self.save_run_info(XP_dict)

            if self.verbose:
                if 'manager_info' in XP_dict:
                    print 'XP started at {}, ended at {}, lasted {} seconds'.format(XP_dict['manager_info']['start_ctime'], XP_dict['manager_info']['end_ctime'], round(XP_dict['manager_info']['duration'], 2))

        # this is the moment to pause all station finished and before placing new droplets
        self.apply_pause()

        # launch station 2, make droplets
        if droplet_XP_dict is not None:
            self.add_temperature_info_to_XP_dict(droplet_XP_dict)
            if 'droplets' in droplet_XP_dict:
                if len(droplet_XP_dict['droplets']) > 0:
                    self._n_xp_with_droplet_done += 1
            self.working_station_dict['make_droplet_station'].make_droplets()  # this is a blocking call

    def add_clean_syringe_XP(self):

        XP_dict = {}
        XP_dict['force_clean_syringe'] = True

        self.add_XP(XP_dict)

    def add_clean_containers_XP(self):

        XP_dict = {}
        XP_dict['min_waiting_time'] = 60

        for _ in range(N_POSITION):
            self.add_XP(XP_dict)

    def add_purge_sequence_XP(self, surfactant_volume=2, n_purge=16):

        XP_dict = {}
        XP_dict['min_waiting_time'] = 60

        XP_dict['oil_formulation'] = {}
        for oil_name in OIL_PUMP_CHEMICALS.values():
            XP_dict['oil_formulation'][oil_name] = 1

        XP_dict['surfactant_volume'] = surfactant_volume
        XP_dict['surfactant_formulation'] = {}
        for surfactant_name in SURFACTANT_PUMP_CHEMICALS.values():
            XP_dict['surfactant_formulation'][surfactant_name] = 1

        #
        for _ in range(n_purge):
            self.add_XP(XP_dict)

    def clean_oil_head(self, n_clean=4):
        if self.xp_queue.any_XP_ongoing() or self.xp_queue.any_XP_waiting():
            print 'XP still running or waiting, for security reasons, we do not allow to run this function!'
            return

        from constants import CLEAN_HEAD_MIXTURE_DOWN

        VOLUME_TUBE = 0.7
        FILL_HEAD_CLEAN_LEVEL = 38
        VOLUME_OIL_CLEAN = 0.1
        VALVE_OIL_CLEAN = 'O'

        INLET_ACETONE = 'E'
        OUTLET_ACETONE_TUBE = 'I'

        for _ in range(n_clean):
            # fill tube with acetone
            self.pump.controller.acetone_oil.pump(VOLUME_TUBE, from_valve=INLET_ACETONE)
            self.robot.CLEAN_HEAD_MIXTURE.move_to(CLEAN_HEAD_MIXTURE_DOWN)
            if self.robot.CLEAN_HEAD_MIXTURE.get_switch_state():
                raise Exception('Clean head oil mixture did not go down, stepper might be broken...')
            self.pump.controller.acetone_oil.wait_until_idle()
            self.pump.controller.acetone_oil.deliver(VOLUME_TUBE, to_valve=OUTLET_ACETONE_TUBE, wait=True)
            self.robot.CLEAN_HEAD_MIXTURE.home()

            # move tube to oil filling station
            for _ in range(4):
                self.robot.rotate_geneva_wheels()

            # clean fill head in acetone
            self.robot.FILL_HEAD_MIXTURE.move_to(FILL_HEAD_CLEAN_LEVEL)
            if self.robot.FILL_HEAD_MIXTURE.get_switch_state():
                raise Exception('Fill head oil mixture did not go down, stepper might be broken...')
            for _ in range(4):
                self.pump.controller.transfer(self.pump.controller.groups['oils'], VOLUME_OIL_CLEAN, from_valve=VALVE_OIL_CLEAN, to_valve=VALVE_OIL_CLEAN)
            self.robot.FILL_HEAD_MIXTURE.home()

            # move tube to cleaning station
            for _ in range(4):
                self.robot.rotate_geneva_wheels()

            # clean
            self.working_station_dict['clean_oil_station'].launch({}, clean_tube=True, clean_syringe=False)
            self.working_station_dict['clean_oil_station'].wait_until_idle()
            clean_oil_waste_volume = self.working_station_dict['clean_oil_station'].get_added_waste_volume()

            total_volume_to_waste = VOLUME_TUBE + clean_oil_waste_volume
            self.add_waste_volume(WASTE_CORRECTION * total_volume_to_waste)

    def clean_surfactant_pump(self):
        if self.xp_queue.any_XP_ongoing() or self.xp_queue.any_XP_waiting():
            print 'XP still running or waiting, for security reasons, we do not allow to run this function!'
            return

        VOLUME_DISH = 3.5
        INLET_WATER = 'I'
        OUTLET_DISH = 'O'
        SYRINGE_VOLUME = self.pump.controller.surfactant.total_volume
        N_SYRINGE_UP_DOWN = 4

        # ensure water all over tubing
        for _ in range(2):
            self.pump.controller.surfactant.transfer(VOLUME_DISH, INLET_WATER, OUTLET_DISH)
            self.robot.rotate_geneva_wheels()

        # go and back N_SYRINGE_UP_DOWN time with water to clean
        self.pump.controller.surfactant.transfer(N_SYRINGE_UP_DOWN * SYRINGE_VOLUME, INLET_WATER, INLET_WATER)

        # ensure to get rid of all remaining by flushing water all over tubing
        for _ in range(2):
            self.pump.controller.surfactant.transfer(VOLUME_DISH, INLET_WATER, OUTLET_DISH)
            self.robot.rotate_geneva_wheels()

        # clean
        for _ in range(4):
            self.working_station_dict['clean_dish_station'].launch({})
            self.working_station_dict['clean_dish_station'].wait_until_idle()
            clean_dish_waste_volume = self.working_station_dict['clean_dish_station'].get_added_waste_volume()

            total_volume_to_waste = VOLUME_DISH + clean_dish_waste_volume
            self.add_waste_volume(WASTE_CORRECTION * total_volume_to_waste)

            self.robot.rotate_geneva_wheels()
