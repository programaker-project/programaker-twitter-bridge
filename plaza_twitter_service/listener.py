import time
import os
import logging
import threading
import traceback


class TweetListenerThread(threading.Thread):
    def __init__(self, bot):
        threading.Thread.__init__(self)
        self.bot = bot

    def start(self):
        threading.Thread.start(self)

    def run(self):
        try:
            self.inner_loop()
        except Exception:
            logging.fatal("Broken inner loop: {}"
                          .format(traceback.format_exc()))

        # Stop the bridge immediately if this is done *for whatever reason*
        os._exit(1)

    def inner_loop(self):
        while 1:
            print("Looop!")
            time.sleep(1)


class TweetListener:
    def __init__(self, api):
        self.api = api
        self.thread = TweetListenerThread(self)

    def start(self):
        self.thread.start()

    def on_update(self, update):
        logging.info("Update: {}".format(update))
        if self.on_message is None:
            return

        self.on_message(update)

    def on_exception(self, exception):
        logging.error(repr(exception))
