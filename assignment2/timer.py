# Methods for Timer
from datetime import datetime
from datetime import timedelta

def millis(dt_now, start_time):
    dt = dt_now - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

class Timer:
    def __init__(self):
        # self.duration = duration
        self.is_running = False

    def start(self):
        '''
        Start the timer
        '''
        self.start_time = datetime.now()
        self.is_running = True
        # if not self.is_running:
        #     self.start_time = datetime.now()
        #     self.is_running = True
        # else:
        #     print("Timer already running!")

    def stop(self):
        '''
        Stops timer and calculates RTT
        '''
        self.is_running = False
        self.rtt = millis(datetime.now(), self.start_time)

    def get_rtt(self):
        return self.rtt

    def check_if_running(self):
        '''
        Returns whether timer is running
        '''
        return self.is_running

    def timeout(self):
        '''
        Whether timeout has occurred or not
        '''
        if not self.check_if_running():
            return False
        else:
            return millis(datetime.now(), self.start_time) >= self.duration

    def get_time_delay(self):
        return millis(datetime.now(), self.start_time)

    def set_duration(self, duration):
        '''
        Duration for timeout in milliseconds
        '''
        self.duration = duration
