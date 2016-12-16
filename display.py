from Queue import Queue
import threading
import neopixel


class Display(threading.Thread):
    def __init__(self, q, loop_time=1.0 / 60):
        self.q = q
        self.timeout = loop_time
        super(Display, self).__init__()

    def onThread(self, function, *args, **kwargs):
        self.q.put((function, args, kwargs))

    def run(self):
        while True:
            try:
                function, args, kwargs = self.q.get(timeout=self.timeout)
                function(*args, **kwargs)
            except Queue.Empty:
                self.idle()

    def idle(self):
        # put the code you would have put in the `run` loop here
        pass

    def start(self, message):
        neopixel.displayImage(message)

    def stop(self):
        neopixel.stopDisplay()
