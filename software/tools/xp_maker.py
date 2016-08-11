import os
import json

import filetools

from filenaming import XP_PARAMS_FILENAME
from filenaming import VIDEO_FILENAME
from filenaming import RUN_INFO_FILENAME

FOLDERNAME_N_DIGIT = 5

DEFAULT_DROPLET_VOLUME = 4

BASIC_XP_DICT = {
    'min_waiting_time': 60,
    'surfactant_volume': 3.5,
    'droplets': [
        {
            'volume': DEFAULT_DROPLET_VOLUME,
            'position': [5, 0]
        },
        {
            'volume': DEFAULT_DROPLET_VOLUME,
            'position': [-5, 0]
        },
        {
            'volume': DEFAULT_DROPLET_VOLUME,
            'position': [0, 5]
        },
        {
            'volume': DEFAULT_DROPLET_VOLUME,
            'position': [0, -5]
        }
    ],
    'formulation': {},
    'video_info': {
        'duration': 90
    },
    'run_info': {}
}


def save_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)


def make_XP_dict(oil_ratios, xp_folder):

    XP_dict = BASIC_XP_DICT

    oil_names = ['octanol', 'octanoic', 'pentanol', 'dep']
    for oil_name in oil_names:
        XP_dict['formulation'][oil_name] = oil_ratios[oil_name]

    XP_dict['run_info']['filename'] = os.path.join(xp_folder, RUN_INFO_FILENAME)

    XP_dict['video_info']['filename'] = os.path.join(xp_folder, VIDEO_FILENAME)

    return XP_dict


def make_and_save_XP_dict(oil_ratios, xp_folder, save_filename):

    XP_dict = make_XP_dict(oil_ratios, xp_folder)
    save_to_json(XP_dict, save_filename)


def generate_XP_foldername(pool_folder, xp_number):
    fname = filetools.generate_n_digit_name(xp_number, n_digit=FOLDERNAME_N_DIGIT)
    return os.path.join(pool_folder, fname)


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


def count_XP_in_pool_folder(pool_folder):
    # a pool folder must contain only XP folder, so we just count the number of folder
    if os.path.exists(pool_folder):
        return len(filetools.list_folders(pool_folder))
    else:
        return 0
