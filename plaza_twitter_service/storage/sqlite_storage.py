import os
import sqlite3
from xdg import XDG_DATA_HOME

DB_PATH_ENV = 'PLAZA_TWITTER_BRIDGE_DB_PATH'
if os.getenv(DB_PATH_ENV, None) is None:
    DATA_DIRECTORY = os.path.join(XDG_DATA_HOME, "plaza", "bridges", "twitter")
    DEFAULT_PATH = os.path.join(DATA_DIRECTORY, 'db.sqlite3')
else:
    DEFAULT_PATH = os.getenv(DB_PATH_ENV)
    DATA_DIRECTORY = os.path.dirname(DEFAULT_PATH)


class DBContext:
    def __init__(self, db, close_on_exit=True):
        self.db = db
        self.close_on_exit = close_on_exit

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, tb):
        if self.close_on_exit:
            self.db.close()


class SqliteStorage:
    def __init__(self, path, multithread=True):
        self.path = path
        self.db = None
        self.multithread = multithread
        self._create_db_if_not_exists()

    def _open_db(self):
        if not self.multithread:
            if self.db is None:
                self.db = sqlite3.connect(self.path)
                self.db.execute('PRAGMA foreign_keys = ON;')
            db = self.db
        else:
            db = sqlite3.connect(self.path)
            db.execute('PRAGMA foreign_keys = ON;')

        return DBContext(db, close_on_exit=not self.multithread)

    def _create_db_if_not_exists(self):
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        with self._open_db() as db:
            c = db.cursor()
            c.execute('''
            CREATE TABLE IF NOT EXISTS LAST_TWEET_BY_USER (
                listener_id VARCHAR(256),
                listened_id VARCHAR(256),
                tweet_id BIGINT,
                PRIMARY KEY(listener_id, listened_id)
            );
            ''')
            db.commit()
            c.close()

    def get_last_tweet_by_user(self, user_id, channel):
        with self._open_db() as db:
            c = db.cursor()
            c.execute('''
            SELECT tweet_id
            FROM LAST_TWEET_BY_USER
            WHERE listener_id=?
            AND   listened_id=?
            ;
            ''', (user_id, channel))
            results = c.fetchall()
            c.close()

            if len(results) == 0:
                return None

            return results[0][0]

    def set_last_tweet_by_user(self, user_id, channel, tweet_id):
        with self._open_db() as db:
            c = db.cursor()
            c.execute('''
            INSERT OR REPLACE INTO
            LAST_TWEET_BY_USER (listener_id, listened_id, tweet_id)
            VALUES (?, ?, ?)
            ;
            ''', (user_id, channel, tweet_id))
            c.close()
            db.commit()


def get_default():
    return SqliteStorage(DEFAULT_PATH)
