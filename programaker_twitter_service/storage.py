import logging
import os
import re

import sqlalchemy
from xdg import XDG_DATA_HOME

from . import models

DB_PATH_ENV = "TWITTER_BRIDGE_DB_PATH"

if os.getenv(DB_PATH_ENV, None) is None:
    # Support old environment variable
    DB_PATH_ENV = "PLAZA_TWITTER_BRIDGE_DB_PATH"

if os.getenv(DB_PATH_ENV, None) is None:
    _DATA_DIRECTORY = os.path.join(XDG_DATA_HOME, "plaza", "bridges", "twitter")
    CONNECTION_STRING = "sqlite:///{}".format(
        os.path.join(_DATA_DIRECTORY, "db.sqlite3")
    )
else:
    CONNECTION_STRING = os.getenv(DB_PATH_ENV)


class EngineContext:
    def __init__(self, engine):
        self.engine = engine
        self.connection = None

    def __enter__(self):
        self.connection = self.engine.connect()
        return self.connection

    def __exit__(self, exc_type, exc_value, tb):
        self.connection.close()


class StorageEngine:
    def __init__(self, engine):
        self.engine = engine

    def _connect_db(self):
        return EngineContext(self.engine)

    def register_user(self, connection_id, token_info, in_add_transaction=None):
        with self._connect_db() as conn:
            access_token, access_token_secret = token_info

            # Create tweeter user
            check = conn.execute(
                sqlalchemy.select([models.TwitterUserRegistration.c.id]).where(
                    models.TwitterUserRegistration.c.twitter_token == access_token
                )
            ).fetchone()

            if check is None:
                op = models.TwitterUserRegistration.insert().values(
                    twitter_token=access_token, twitter_token_secret=access_token_secret
                )
                result = conn.execute(op)
                twitter_user_id = result.inserted_primary_key[0]
            else:
                twitter_user_id = check.id

            # Create programaker user
            check = conn.execute(
                sqlalchemy.select([models.PlazaUsers.c.id]).where(
                    models.PlazaUsers.c.id == connection_id
                )
            ).fetchone()

            if check is None:
                insert = models.PlazaUsers.insert().values(id=connection_id)
                conn.execute(insert)

            # Bind the two users
            check = conn.execute(
                sqlalchemy.select([models.PlazaUsersInTwitter.c.twitter_id]).where(
                    models.PlazaUsersInTwitter.c.twitter_id == twitter_user_id
                )
            ).fetchone()

            if check is None:
                if in_add_transaction is not None:
                    in_add_transaction(conn, twitter_user_id)

                insert = models.PlazaUsersInTwitter.insert().values(
                    plaza_id=connection_id, twitter_id=twitter_user_id
                )
                conn.execute(insert)
                return True
            else:
                return False

    def get_consumer_key(self, connection_id):
        with self._connect_db() as conn:
            join = sqlalchemy.join(
                models.TwitterUserRegistration,
                models.PlazaUsersInTwitter,
                models.TwitterUserRegistration.c.id
                == models.PlazaUsersInTwitter.c.twitter_id,
            )

            results = conn.execute(
                sqlalchemy.select(
                    [
                        models.TwitterUserRegistration.c.twitter_token,
                        models.TwitterUserRegistration.c.twitter_token_secret,
                    ]
                )
                .select_from(join)
                .where(models.PlazaUsersInTwitter.c.plaza_id == connection_id)
            ).fetchall()

            return [dict(zip(["token", "token_secret"], row)) for row in results]

    def get_last_tweet_by_user(self, user_id, channel):
        with self._connect_db() as conn:
            result = conn.execute(
                sqlalchemy.select([models.LastTweetByUser.c.tweet_id]).where(
                    sqlalchemy.and_(
                        models.LastTweetByUser.c.listener_id == user_id,
                        models.LastTweetByUser.c.listened_id == channel,
                    )
                )
            ).fetchone()

            if result is None:
                return None

            return result[0]

    def set_last_tweet_by_user(self, user_id, channel, tweet_id):
        with self._connect_db() as conn:
            # TODO: Refactor with the one above
            result = conn.execute(
                sqlalchemy.select([models.LastTweetByUser.c.tweet_id]).where(
                    sqlalchemy.and_(
                        models.LastTweetByUser.c.listener_id == user_id,
                        models.LastTweetByUser.c.listened_id == channel,
                    )
                )
            ).fetchone()

            if result is None:
                op = models.LastTweetByUser.insert().values(
                    listener_id=user_id, listened_id=channel, tweet_id=tweet_id
                )
            else:
                op = (
                    models.LastTweetByUser.update()
                    .where(
                        sqlalchemy.and_(
                            models.LastTweetByUser.c.listener_id == user_id,
                            models.LastTweetByUser.c.listened_id == channel,
                        )
                    )
                    .values(tweet_id=tweet_id)
                )

            conn.execute(op)

    def get_last_timeline_tweet_by_user(self, user_id):
        with self._connect_db() as conn:
            result = conn.execute(
                sqlalchemy.select([models.LastTweetInUserTimeline.c.tweet_id]).where(
                    models.LastTweetByUser.c.listener_id == user_id
                )
            ).fetchone()

            if result is None:
                return None

            return result[0]

    def set_last_timeline_tweet_by_user(self, user_id, tweet_id):
        with self._connect_db() as conn:
            # TODO: Refactor with the one above
            result = conn.execute(
                sqlalchemy.select([models.LastTweetInUserTimeline.c.tweet_id]).where(
                    models.LastTweetInUserTimeline.c.listener_id == user_id
                )
            ).fetchone()

            if result is None:
                op = models.LastTweetInUserTimeline.insert().values(
                    listener_id=user_id, tweet_id=tweet_id
                )
            else:
                op = (
                    models.LastTweetInUserTimeline.update()
                    .where(models.LastTweetInUserTimeline.c.listener_id == user_id)
                    .values(tweet_id=tweet_id)
                )

            conn.execute(op)

    def get_twitter_user_id(self, user_id):
        with self._connect_db() as conn:
            result = conn.execute(
                sqlalchemy.select([models.PlazaUsersInTwitter.c.twitter_id]).where(
                    models.PlazaUsersInTwitter.c.plaza_id == user_id
                )
            ).fetchone()

            return result.twitter_id

    def get_followers(self, twitter_id):
        with self._connect_db() as conn:
            results = conn.execute(
                sqlalchemy.select([models.TwitterFollows.c.follower_id]).where(
                    models.TwitterFollows.c.followed_id == twitter_id
                )
            ).fetchall()

            return map(lambda x: x.follower_id, results)

    def is_follower(self, twitter_id, follower_id):
        with self._connect_db() as conn:
            result = conn.execute(
                sqlalchemy.select([models.TwitterFollows.c.follower_id]).where(
                    sqlalchemy.and_(
                        models.TwitterFollows.c.followed_id == twitter_id,
                        models.TwitterFollows.c.follower_id == follower_id,
                    )
                )
            ).fetchone()

            return result is not None

    def _initialize_followers(self, conn, twitter_id, followers):
        conn.execute(
            models.TwitterFollows.insert(),
            [
                dict(followed_id=twitter_id, follower_id=follower,)
                for follower in followers
            ],
        )

    def get_all_users(self):
        with self._connect_db() as conn:
            # These are seected from PlazaUsersInTwitter to avoid the ones which
            # have no established connections.
            results = conn.execute(
                sqlalchemy.select([models.PlazaUsersInTwitter.c.plaza_id])
            ).fetchall()

            return map(lambda x: x.plaza_id, results)

    def add_follower(self, twitter_id, follower_id):
        with self._connect_db() as conn:
            op = models.TwitterFollows.insert().values(
                followed_id=twitter_id, follower_id=follower_id
            )

            conn.execute(op)

    def remove_follower(self, twitter_id, follower_id):
        with self._connect_db() as conn:
            op = models.TwitterFollows.delete().where(
                sqlalchemy.and_(
                    models.TwitterFollows.c.followed_id == twitter_id,
                    models.TwitterFollows.c.follower_id == follower_id,
                )
            )

            conn.execute(op)


def get_engine():
    # Create path to SQLite file, if its needed.
    if CONNECTION_STRING.startswith("sqlite"):
        db_file = re.sub("sqlite.*:///", "", CONNECTION_STRING)
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

    engine = sqlalchemy.create_engine(CONNECTION_STRING)
    metadata = models.metadata
    metadata.create_all(engine)

    return StorageEngine(engine)
