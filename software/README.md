## Software

This code implemented and orchestrates all the working stations, that are specialized modules implemented as threads and able to performs one simple task well, into a fully functional platform able to accept experimental files and execute them in a parallel fashion.

The [manager.py](manager.py) file is the entry point and only file to import for using Dropfactory. It ocntains a ```add_XP(XP_dict)``` function that adds an experimental configuration (```XP_dict```) to the manager. The ```XP_dict``` can be created as showed in [xp_maker.py](tools/xp_maker.py).

### Experiment description

An experiment is fully described by a json file with the following fields. Note that there are helper tools to build such file in [xp_maker.py](tools/xp_maker.py).

```python
EXAMPLE_XP_DICT = {
    # Dropfactory outputs some informaiton about the experimental conditions, such as the time of the day
    # it was run, the temperature, the humidity. The 'run_info' field tell the platform where to save
    # that information for this particualr experiment. If the experiment video will be stored place in
    # the "xp_folder" folder, a good practice is to save it at the same place.
    # By convention we use RUN_INFO_FILENAME = 'run_info.json' (see software/tools/filenaming.py)
    'run_info': {
        'filename': os.path.join(xp_folder, RUN_INFO_FILENAME)
    },
    # 'min_waiting_time' is the minimum time a dish should stay at any station,
    # this is to ensure proper drying at the drying stations.
    'min_waiting_time': 60,  # in seconds
    # 'video_info' tells the platform how long the record an experiment for and where to save that video.
    # As with he 'run_info' field, it is a good practice is to save it at the same place.
    # By convention we use VIDEO_FILENAME = 'video.avi' (see software/tools/filenaming.py)
    'video_info': {
        'filename': os.path.join(xp_folder, VIDEO_FILENAME)
        'duration': 90  # in seconds
    },
    # 'arena_type' tell what type of dish the experiment should be using. Dish should be changed manually,
    # only one dish type can be present at the same time on the platform and the ARENA_TYPE field should
    # be changed accordingly in software/constants.py. This field is mostly a security/memory field,
    # we never used other dishes that a plain glass petri_dish.
    'arena_type': 'petri_dish',
    # 'oil_formulation' describe the composition of the oil droplets.
    # The number will be normalized to sum to 1.0.
    # The association between the compounds and the associated pumps is defined in software/constants.py.
    # Changes should be reported there accordingly.
    'oil_formulation': {
        'dep': 0.36,
        'octanol': 0.29,
        'octanoic': 0.0,
        'pentanol': 0.33
    },
    ## 'surfactant_volume' how much aqueous phase to pour in the dish
    'surfactant_volume': 3.5,  # in mL
    # 'surfactant_formulation' is similar 'oil_formulation' but for the aqueous phase,
    # which can be a mixture of multiple aqueous phases. The number will be normalized to sum to 1.0.
    # As for oils, the association between the compounds and the associated pumps is defined
    # in software/constants.py. Changes should be reported there accordingly.
    'surfactant_formulation': {
        'TTAB': 1.0
    },
    # 'droplets' is the placement information for droplet, it is a list where each elements
    # corresponds to one droplet. Each droplets is then described by its 'volume' and 'position'.
    # 'volume' is in uL and 'position' is in mm relative to the center of the dish.
    # Here we have 4 droplets, one at the center and three equally spread around on a circle of radius 5mm.
    # DEFAULT_DROPLET_VOLUME = 4 uL.
    'droplets': [
        {
            'volume': DEFAULT_DROPLET_VOLUME, # in uL
            'position': [0, 0] # relative position in mm from the dish center
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
```

### Repository organization

The code is segmented by functionalities as follows:

- [arduino](arduino) holds the firmware for the two arduino boards that are used to control the all platform. It is based on our [Arduino-CommandTools](https://github.com/croningp/Arduino-CommandTools) that allows to quickly and flexibly prototype Arduino based robots.
- [pump](pump) holds the pump configurations for the 10 Tricontinent C3000 pumps used to handle liquids used for droplet experiments. That is oils and aqueous phases + waste management + cleaning liquids (acetone and water). It make use of our easy to use [pycont](https://github.com/croningp/pycont) python library.
- [robot](robot) contains all the utilities to actuate the platform. Such as rotating the geneva wheels or precisely pumping and deliver liquid via our syringe systems. It is base on our [commanduino](https://github.com/croningp/commanduino) tool-kit that allows to quickly and flexibly control Arduino based robot through Python.
- [tools](tools) holds various tools used to manage and organize dropfactory. The most important file is [xp_manager.py](tools/xp_manager.py) that orchestrate the parallelized operation of the robot.
- [webcam](webcam) contains the camera configuration for the MICROSOFT 6CH-00002 we use to video record the droplets. It is based on our [chemobot_tools](https://github.com/croningp/chemobot_tools) library used to detect and analyse droplets.
- [working_station](working_station) contains all the individuals working station that fulfil a single task such as cleaning the oil containers, or placing droplet with the syringe. Those stations are implemented as threads and orchestrated by the [xp_manager.py](tools/xp_manager.py) in the [tools](tools) folder.

Finally the remaining files are helpers I used while developing the platform.
