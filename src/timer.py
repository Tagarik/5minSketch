import threading

class Timer:
    def __init__(self):
        self.interval = 5
        self.callback = None
        self.timer = None
        self.running = False

    def set_timer_callback(self, callback):
        self.callback = callback

    def start(self, interval):
        self.interval = interval
        self.running = True
        self._start_timer()

    def _start_timer(self):
        if self.running:
            self.timer = threading.Timer(self.interval, self._timer_complete)
            self.timer.start()

    def _timer_complete(self):
        if self.callback:
            self.callback()
        self._start_timer()

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.cancel()

    def reset(self):
        self.stop()
        self.start(self.interval)