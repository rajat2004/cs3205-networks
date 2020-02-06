# Methods for Timer
import time

from datetime import datetime
from datetime import timedelta

def millis(dt_now, start_time):
    dt = dt_now - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

class Timer:
    # duration in milliseconds
    def __init__(self, duration):
        self.duration = duration

    def start(self):
        self.start_time = datetime.now()
        self.is_running = True

    def stop(self):
        self.is_running = False

    def check_if_running(self):
        return self.is_running

    def timeout(self):
        if not self.check_if_running():
            return False
        else:
            return millis(datetime.now(), self.start_time) >= self.duration

    def get_time_delay(self):
        return millis(datetime.now(), self.start_time)
