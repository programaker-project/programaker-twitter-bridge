import tweepy


class AuthHandler:
    def __init__(self, config, storage):
        self.config = config
        self.storage = storage

    def get_api(self, connection_id):
        access_data = self.storage.get_consumer_key(connection_id)[0]

        auth = tweepy.OAuthHandler(
            self.config.get_twitter_token(), self.config.get_twitter_token_secret()
        )
        auth.set_access_token(access_data["token"], access_data["token_secret"])
        return tweepy.API(auth)
