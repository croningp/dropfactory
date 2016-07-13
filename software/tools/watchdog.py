import time
import threading

SLEEP_TIME = 0.1


class Watchdog(threading.Thread):

    def __init__(self, timeout_in_sec, callback):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.raised = False

        self.timeout_in_sec = timeout_in_sec
        self.callback = callback
        self.start()

    def stop(self):
        self.interrupted.release()

    def run(self):
        self.interrupted.acquire()
        self.ping()
        while self.interrupted.locked():
            if not self.raised:
                if self.time_since_last_ping > self.timeout_in_sec:
                    self.callback()
                    self.raised = True
            time.sleep(SLEEP_TIME)

    def reset(self):
        self.ping()
        self.raised = False

    def ping(self):
        self.last_ping = time.time()

    @property
    def time_since_last_ping(self):
        return time.time() - self.last_ping
