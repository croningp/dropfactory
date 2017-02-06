# this file contains constant vlaue that are shared between different scripts

# number of position
N_POSITION = 8

# petri dish cleaning
CLEAN_HEAD_DISH_DOWN = 15
CLEAN_HEAD_DISH_MAX = 16

# tube mixture of oil cleaning
CLEAN_HEAD_MIXTURE_DOWN = 28
CLEAN_HEAD_MIXTURE_MAX = 30

# oil filling station
TUBE_OIL_VOLUME = 0.5  # mL
FILL_HEAD_MIXTURE_MAX = 40

#surfactant filling station
MAX_SURFACTANT_VOLUME = 4  # mL

#
XY_ABOVE_VIAL = [95, 14]
XY_ABOVE_TUBE = [53, 73]
XY_ABOVE_DISH = [134, 74]
Z_FREE_LEVEL = 110

# current chemicals
OIL_PUMP_CHEMICALS =  {
    'oil_1': 'dep',
    'oil_2': 'octanoic',
    'oil_3': 'octanol',
    'oil_4': 'pentanol'
}

SURFACTANT_PUMP_CHEMICALS = {
    'surfactant': 'TTAB'
}
