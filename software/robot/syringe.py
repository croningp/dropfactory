

class Syringe(object):

    def __init__(self, axis_device, empty_level):
        # axis device should be calibrated in uL units, with min and max well defined for security, even if this layer adds additonal security
        self.axis = axis_device
        self.empty_level = empty_level
        self.total_volume = empty_level

    def home(self, wait=True):
        self.axis.home(wait=wait)

    def init(self):
        self.home()
        self.go_to_volume(0)
        self.current_volume = 0

    def volume_to_position(self, volume_in_uL):
        return self.empty_level - volume_in_uL

    @property
    def remaining_volume(self):
        return self.total_volume - self.current_volume

    def is_volume_valid(self, volume_in_uL):
        return 0 <= volume_in_uL <= self.total_volume

    def wait_until_idle(self):
        self.axis.wait_until_idle()

    def go_to_volume(self, volume_in_uL, wait=True):
        # hard security here, we do not handle wrong user behavior and just throw an exception
        if not self.is_volume_valid(volume_in_uL):
            raise Exception('Volume {} is not valid'.format(volume_in_uL))

        # we wait in case a previous command did not finished
        self.wait_until_idle()

        position = self.volume_to_position(volume_in_uL)
        self.axis.move_to(position, wait=wait)
        self.current_volume = volume_in_uL

    def pump(self, volume_in_uL, wait=True):
        self.go_to_volume(self.current_volume + volume_in_uL, wait=wait)

    def deliver(self, volume_in_uL, wait=True):
        self.go_to_volume(self.current_volume - volume_in_uL, wait=wait)
