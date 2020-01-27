import time
import os
import logging
import threading
import traceback


# See https://developer.twitter.com/en/docs/basics/rate-limits for more info

TIMELINE_RATE_LIMIT_AMOUNT = 900
TIMELINE_RATE_LIMIT_WINDOW_SECS = 15 * 60  # 15 Minutes

# How much "free-space" should be left for non-accounted additions.
# Later added checks can get some slack from this margin
RATE_LIMIT_MARGIN = 0.5

MIN_UPDATE_PERIOD = 60  # Minimal time between updates on a single user account
NUM_TWEETS_PER_CHECK = 3  # How many tweets are retrieved in a single check

assert 0 < RATE_LIMIT_MARGIN < 1


class TweetListenerThread(threading.Thread):
    def __init__(self, bot):
        threading.Thread.__init__(self)
        self.bot = bot
        self.by_user = {}
        self.to_check = {}

    def start(self):
        threading.Thread.start(self)

    def add_to_user(self, user, subkey):
        logging.debug("New listener: {} {}".format(user, subkey))
        if user not in self.by_user:
            self.by_user[user] = {}
        self.by_user[user][subkey] = None

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
            self.do_checks()
            time.sleep(1)

    def do_checks(self):
        for user_id, user_data in self.by_user.items():
            user_update_period = (((TIMELINE_RATE_LIMIT_WINDOW_SECS / TIMELINE_RATE_LIMIT_AMOUNT)
                                   / RATE_LIMIT_MARGIN)
                                  * len(user_data))

            for channel, last_check_time in user_data.items():

                time_to_update = False
                if last_check_time is None:
                    time_to_update = True
                else:
                    time_since_update = time.time() - last_check_time
                    time_to_update = ((time_since_update > MIN_UPDATE_PERIOD)
                                      and (time_since_update > user_update_period))

                if time_to_update:
                    self.check(user_id, channel)
                    user_data[channel] = time.time()

    def check(self, user_id, channel):
        logging.debug("Checking update for {} on {}".format(user_id, channel))
        self.bot.check(user_id, channel)


class TweetListener:
    def __init__(self, api, storage):
        self.api = api
        self.thread = TweetListenerThread(self)
        self.storage = storage

    def add_to_user(self, user, subkey):
        self.thread.add_to_user(user, subkey)

    def check(self, user_id, channel):
        tweets = self.api.user_timeline(channel, count=NUM_TWEETS_PER_CHECK)
        last_tweet_by_user = self.storage.get_last_tweet_by_user(user_id, channel) or 0
        for tweet in tweets[::-1]:
            tweet_id = tweet._json['id']
            if tweet_id > last_tweet_by_user:
                self.storage.set_last_tweet_by_user(user_id, channel, tweet_id)
                self.on_update(user_id, tweet)

    def start(self):
        self.thread.start()

    def on_update(self, user_id, update):
        if self.on_message is None:
            return
        self.on_message(user_id, update)
        time.sleep(0.5)

    def on_exception(self, exception):
        logging.error(repr(exception))
