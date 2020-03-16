import time
import os
import logging
import threading
import traceback
from . import rate_limit

NUM_TWEETS_PER_CHECK = 3  # How many tweets are retrieved in a single check

class TweetListenerThread(threading.Thread):
    def __init__(self, bot, rate_limit_manager):
        threading.Thread.__init__(self)
        self.bot = bot
        self.rate_limit_manager = rate_limit_manager
        self.by_user = {}
        self.to_check = {}
        self.timelines = set()

    def start(self):
        threading.Thread.start(self)

    def add_to_user(self, user, subkey):
        logging.debug("New listener: {} {}".format(user, subkey))
        if user not in self.by_user:
            self.by_user[user] = []
        self.by_user[user].append(subkey)

    def add_home_timeline(self, user):
        logging.debug("New home timeline: {}".format(user))
        self.timelines.add(user)

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
            self.check_timelines()
            self.check_monitors()
            time.sleep(1)

    def check_timelines(self):
        for user_id in self.timelines:
            if self.rate_limit_manager.time_for_periodic_check(
                    user_id,
                    rate_limit.HOME_TIMELINE,
                    1
            ):
                try:
                    self.check_timeline(user_id)
                except Exception:
                    logging.error(traceback.format_exc())

    def check_monitors(self):
        for user_id, user_channels in self.by_user.items():
            for channel in user_channels:
                if self.rate_limit_manager.time_for_periodic_check(
                        user_id,
                        rate_limit.USER_TIMELINE,
                        len(user_channels),
                        channel,
                ):
                    try:
                        self.check(user_id, channel)
                    except Exception:
                        logging.error(traceback.format_exc())


    def check(self, user_id, channel):
        logging.debug("Checking update for {} on {}".format(user_id, channel))
        self.bot.check(user_id, channel)


    def check_timeline(self, user_id):
        logging.debug("Checking timeline update for {}".format(user_id))
        self.bot.check_timeline(user_id)


class TweetListener:
    def __init__(self, api_dispatcher, storage, rate_limit_manager):
        self.api_dispatcher = api_dispatcher
        self.thread = TweetListenerThread(self, rate_limit_manager)
        self.storage = storage

    def add_to_user(self, user, subkey):
        self.thread.add_to_user(user, subkey)

    def add_home_timeline(self, user):
        self.thread.add_home_timeline(user)

    def check(self, user_id, channel):
        tweets = self.api_dispatcher.get_api(user_id).user_timeline(channel, count=NUM_TWEETS_PER_CHECK)
        last_tweet_by_user = self.storage.get_last_tweet_by_user(user_id, channel) or 0
        for tweet in tweets[::-1]:
            tweet_id = tweet._json['id']
            if tweet_id > last_tweet_by_user:
                self.storage.set_last_tweet_by_user(user_id, channel, tweet_id)
                self.on_update(user_id, tweet)

    def check_timeline(self, user_id):
        last_timeline_tweet_id = self.storage.get_last_timeline_tweet_by_user(user_id) or None
        tweets = self.api_dispatcher.get_api(user_id).home_timeline(since_id=last_timeline_tweet_id)
        for tweet in tweets[::-1]:
            tweet_id = tweet._json['id']
            self.storage.set_last_timeline_tweet_by_user(user_id, tweet_id)
            self.on_timeline_update(user_id, tweet)

    def start(self):
        self.thread.start()

    def on_update(self, user_id, update):
        if self.on_message is None:
            return
        self.on_message(user_id, update)
        time.sleep(0.5)

    def on_exception(self, exception):
        logging.error(repr(exception))
