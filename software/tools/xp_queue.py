from collections import deque


class XPQueue(object):

    def __init__(self, queue_size):
        self.queue_size = queue_size
        self.XP_waiting = deque()
        self.XP_ongoing = deque([None] * queue_size, maxlen=queue_size)

    def add_XP(self, XP_dict):
        self.XP_waiting.append(XP_dict)

    def remove_XP(self, XP_dict):
        self.XP_waiting.remove(XP_dict)

    def empty_XP_waiting(self):
        self.XP_waiting.clear()

    def any_XP_waiting(self):
        return len(self.XP_waiting) > 0

    def any_XP_ongoing(self):
        return self.XP_ongoing.count(None) != self.queue_size

    def get_XP_ongoing(self, ongoing_XP_number):
        if 0 <= ongoing_XP_number <= self.queue_size - 1:
            ind = self.queue_size - 1 - ongoing_XP_number
            return self.XP_ongoing[ind]
        else:
            raise IndexError('ongoing_XP_number out of range')

    def cycle(self):
        if len(self.XP_waiting) > 0:
            XP_dict = self.XP_waiting.popleft()
        else:
            XP_dict = None
        self.XP_ongoing.append(XP_dict)
