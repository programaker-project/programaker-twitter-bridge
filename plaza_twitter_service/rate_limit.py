import logging
import time

# Information from https://developer.twitter.com/en/docs/basics/rate-limits
SECONDS = 1
MINUTES = 60 * SECONDS
HOURS = 60 * MINUTES

# How much "free-space" should be left for non-accounted additions.
# Later added checks can get some slack from this margin
RATE_LIMIT_MARGIN = 0.5
assert 0 < RATE_LIMIT_MARGIN < 1

MIN_UPDATE_PERIOD = 60 * SECONDS # Minimal time between updates on a single user account

# Endpoint information
USER_TIMELINE = 'statuses/user_timeline'

ENDPOINTS = {
    # POST
    "statuses/update": { "limit_window": 3*HOURS, "per_user_limit": 300, "group": "create_content" },
    "statuses/retweet/:id": { "limit_window": 3*HOURS, "per_user_limit": 300, "group": "create_content" },
    "favorites/create/": { "limit_window": 24*HOURS, "per_user_limit": 1000 },
    "friendships/create/": { "limit_window": 24*HOURS, "per_user_limit": 400 },
    "direct_messages/events/new/": { "limit_window": 24*HOURS, "per_user_limit": 1000 },

    # GET
    "account/verify_credentials":{ "limit_window": 15*MINUTES, "per_user_limit": 75 },
    "application/rate_limit_status":{ "limit_window": 15*MINUTES, "per_user_limit": 180},
    "favorites/list":{ "limit_window": 15*MINUTES, "per_user_limit": 75 },
    "followers/ids":{ "limit_window": 15*MINUTES, "per_user_limit": 15 },
    "followers/list":{ "limit_window": 15*MINUTES, "per_user_limit": 15},
    "friends/ids":{ "limit_window": 15*MINUTES, "per_user_limit": 15 },
    "friends/list":{ "limit_window": 15*MINUTES, "per_user_limit": 15 },
    "friendships/show":{ "limit_window": 15*MINUTES, "per_user_limit": 180},
    "geo/id/:place_id":{ "limit_window": 15*MINUTES, "per_user_limit": 75 },
    "help/configuration":{ "limit_window": 15*MINUTES, "per_user_limit": 15},
    "help/languages":{ "limit_window": 15*MINUTES, "per_user_limit": 15 },
    "help/privacy":{ "limit_window": 15*MINUTES, "per_user_limit": 15 },
    "help/tos":{ "limit_window": 15*MINUTES, "per_user_limit": 15 },
    "lists/list":{ "limit_window": 15*MINUTES, "per_user_limit": 15},
    "lists/members":{ "limit_window": 15*MINUTES, "per_user_limit": 900 },
    "lists/members/show":{ "limit_window": 15*MINUTES, "per_user_limit": 15},
    "lists/memberships":{ "limit_window": 15*MINUTES, "per_user_limit": 75 },
    "lists/ownerships":{ "limit_window": 15*MINUTES, "per_user_limit": 15 },
    "lists/show":{ "limit_window": 15*MINUTES, "per_user_limit": 75 },
    "lists/statuses":{ "limit_window": 15*MINUTES, "per_user_limit": 900},
    "lists/subscribers":{ "limit_window": 15*MINUTES, "per_user_limit": 180},
    "lists/subscribers/show":{ "limit_window": 15*MINUTES, "per_user_limit": 15},
    "lists/subscriptions":{ "limit_window": 15*MINUTES, "per_user_limit": 15 },
    "search/tweets":{ "limit_window": 15*MINUTES, "per_user_limit": 180 },
    "statuses/lookup":{ "limit_window": 15*MINUTES, "per_user_limit": 900},
    "statuses/mentions_timeline":{ "limit_window": 15*MINUTES, "per_user_limit": 75},
    "statuses/retweeters/ids":{ "limit_window": 15*MINUTES, "per_user_limit": 75 },
    "statuses/retweets_of_me":{ "limit_window": 15*MINUTES, "per_user_limit": 75},
    "statuses/retweets/:id":{ "limit_window": 15*MINUTES, "per_user_limit": 75 },
    "statuses/show/:id":{ "limit_window": 15*MINUTES, "per_user_limit": 900 },
    "statuses/user_timeline":{ "limit_window": 15*MINUTES, "per_user_limit": 900},
    "trends/available":{ "limit_window": 15*MINUTES, "per_user_limit": 75 },
    "trends/closest":{ "limit_window": 15*MINUTES, "per_user_limit": 75},
    "trends/place":{ "limit_window": 15*MINUTES, "per_user_limit": 75},
    "users/lookup":{ "limit_window": 15*MINUTES, "per_user_limit": 900},
    "users/search":{ "limit_window": 15*MINUTES, "per_user_limit": 900},
    "users/show":{ "limit_window": 15*MINUTES, "per_user_limit": 900},
    "users/suggestions":{ "limit_window": 15*MINUTES, "per_user_limit": 15},
    "users/suggestions/:slug":{ "limit_window": 15*MINUTES, "per_user_limit": 15},
    "users/suggestions/:slug/members":{ "limit_window": 15*MINUTES, "per_user_limit": 15},
}

class RateLimitManager:
    def __init__(self):
        self.usage_info = {}

    def notify_will_use(self, connection_id, endpoint):
        if connection_id not in self.usage_info:
            self.usage_info[connection_id] = {}

        if endpoint not in self.usage_info[connection_id]:
            self.usage_info[connection_id][endpoint] = { 'active': None, 'check': {}}

        self.usage_info[connection_id][endpoint]['active'] = time.time()

    def time_for_periodic_check(self, connection_id, endpoint, queries_in_bucket, queried_element=None):
        endpoint_info = ENDPOINTS[endpoint]
        bucket = endpoint_info.get('group', endpoint)

        single_check_update_period = ((endpoint_info['limit_window'] / endpoint_info['per_user_limit'])
                                      / RATE_LIMIT_MARGIN)
        per_element_update_period = (single_check_update_period * queries_in_bucket)

        if connection_id not in self.usage_info:
            self.usage_info[connection_id] = {}

        if endpoint not in self.usage_info[connection_id]:
            self.usage_info[connection_id][endpoint] = { 'active': None, 'check': {}}

        last_time_checked = self.usage_info[connection_id][endpoint]['check'].get(queried_element, None)

        time_to_update = False
        if last_time_checked is None:
            time_to_update = True
        else:
            time_since_update = time.time() - last_time_checked
            time_to_update = ((time_since_update > MIN_UPDATE_PERIOD)
                              and (time_since_update > per_element_update_period))

        if time_to_update:
            self.usage_info[connection_id][endpoint]['check'][queried_element] = time.time()

        return time_to_update
