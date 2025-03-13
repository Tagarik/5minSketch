import threading

class Timer:
    def __init__(self):
        self.interval = 5
        self.callback = None
        self.timer = None
        self.running = False
        self.remaining_time = 0

    def set_timer_callback(self, callback):
        self.callback = callback

    def start(self, interval):
        self.interval = interval
        self.remaining_time = interval
        self.running = True
        self._start_timer()

    def _start_timer(self):
        if self.running:
            self.timer = threading.Timer(1, self._timer_tick)
            self.timer.start()

    def _timer_tick(self):
        if self.running:
            self.remaining_time -= 1
            if self.callback:
                self.callback(self.remaining_time)
            if self.remaining_time <= 0:
                self.remaining_time = self.interval
            self._start_timer()

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.cancel()

    def reset(self):
        self.stop()
        self.start(self.interval)