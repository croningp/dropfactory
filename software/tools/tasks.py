import time
import threading

SLEEP_TIME = 0.1


class Task(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.interrupted = threading.Lock()

        self.XP_dict = None
        self.running = False

    def run(self):
        self.interrupted.acquire()
        while self.interrupted.locked():
            if self.running:
                self.main()
                self.running = False
            else:
                time.sleep(SLEEP_TIME)

    def stop(self):
        self.interrupted.release()

    def launch(self, XP_dict):
        self.XP_dict = XP_dict
        self.running = True

    def wait_until_idle(self):
        while self.running:
            time.sleep(SLEEP_TIME)

    def main(self):
        raise NotImplementedError
