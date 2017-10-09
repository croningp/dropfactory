import os
import json

import filetools

from filenaming import XP_PARAMS_FILENAME
from filenaming import VIDEO_FILENAME
from filenaming import RUN_INFO_FILENAME

FOLDERNAME_N_DIGIT = 5

DEFAULT_DROPLET_VOLUME = 4

BASIC_XP_DICT = {
    'run_info': {},
    'min_waiting_time': 60,  # s
    'video_info': {
        'duration': 90  # s
    },
    'arena_type': 'petri_dish',
    'oil_formulation': {},
    'surfactant_volume': 3.5,  # mL
    'surfactant_formulation': {'TTAB': 1.0}, # those are ratios
    'droplets': [
        {
            'volume': DEFAULT_DROPLET_VOLUME,
            'position': [0, 0]
        },
        {
            'volume': DEFAULT_DROPLET_VOLUME,
            'position': [-5, 0]
        },
        {
            'volume': DEFAULT_DROPLET_VOLUME,
            'position': [2.5, 4.33]
        },
        {
            'volume': DEFAULT_DROPLET_VOLUME,
            'position': [2.5, -4.33]
        }
    ]
}


## generic functions

def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)


def generate_XP_foldername(pool_folder, xp_number):
    fname = filetools.generate_n_digit_name(xp_number, n_digit=FOLDERNAME_N_DIGIT)
    return os.path.join(pool_folder, fname)


def make_basic_XP_dict(xp_folder):
    XP_dict = BASIC_XP_DICT
    XP_dict['run_info']['filename'] = os.path.join(xp_folder, RUN_INFO_FILENAME)
    XP_dict['video_info']['filename'] = os.path.join(xp_folder, VIDEO_FILENAME)
    return XP_dict

def save_XP_dict_to_folder(XP_dict, xp_folder):
    # make the XP_dict and save it there
    filetools.ensure_dir(xp_folder)
    XP_filename = os.path.join(xp_folder, XP_PARAMS_FILENAME)
    save_to_json(XP_dict, XP_filename)


def generate_next_XP_foldername(pool_folder, n_digit=FOLDERNAME_N_DIGIT):
    # save incremetaly in pool_folder
    # ensure pool_folder exist and create incremetal foldername
    filetools.ensure_dir(pool_folder)
    return filetools.generate_incremental_foldername(pool_folder, n_digit=n_digit)


def count_XP_in_pool_folder(pool_folder):
    # a pool folder must contain only XP folder, so we just count the number of folder
    if os.path.exists(pool_folder):
        return len(filetools.list_folders(pool_folder))
    else:
        return 0

## specialized one for oil_ratios, older, need to keep naming

def make_XP_dict(oil_ratios, xp_folder):

    XP_dict = BASIC_XP_DICT
    XP_dict['run_info']['filename'] = os.path.join(xp_folder, RUN_INFO_FILENAME)
    XP_dict['video_info']['filename'] = os.path.join(xp_folder, VIDEO_FILENAME)
    XP_dict['oil_formulation'] = oil_ratios

    return XP_dict

def make_and_save_XP_dict(oil_ratios, xp_folder, save_filename):

    XP_dict = make_XP_dict(oil_ratios, xp_folder)
    save_to_json(XP_dict, save_filename)

def save_XP_to_folder(oil_ratios, xp_folder):
    # make the XP_dict and save it there
    filetools.ensure_dir(xp_folder)
    XP_filename = os.path.join(xp_folder, XP_PARAMS_FILENAME)
    make_and_save_XP_dict(oil_ratios, xp_folder, XP_filename)


def add_XP_to_pool_folder(oil_ratios, pool_folder, n_digit=FOLDERNAME_N_DIGIT):
    # save incremetaly in pool_folder
    # ensure pool_folder exist and create incremetal foldername
    filetools.ensure_dir(pool_folder)
    xp_folder = filetools.generate_incremental_foldername(pool_folder, n_digit=n_digit)
    save_XP_to_folder(oil_ratios, xp_folder)
