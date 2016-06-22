import os
import json

import filetools

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

    XP_dict['run_info']['filename'] = os.path.join(xp_folder, 'run_info.json')

    XP_dict['video_info']['filename'] = os.path.join(xp_folder, 'video.avi')

    return XP_dict


def make_and_save_XP_dict(oil_ratios, xp_folder, save_filename):

    XP_dict = make_XP_dict(oil_ratios, xp_folder)
    save_to_json(XP_dict, save_filename)


def add_XP_to_pool_folder(oil_ratios, pool_folder, n_digit=5):
    # ensure pool_folder exist and create incremetal foldername
    filetools.ensure_dir(pool_folder)
    xp_folder = filetools.generate_incremental_foldername(pool_folder, n_digit=n_digit)
    filetools.ensure_dir(xp_folder)
    # make the XP_dict and save it there
    XP_filename = os.path.join(xp_folder, 'params.json')
    make_and_save_XP_dict(oil_ratios, xp_folder, XP_filename)
