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
        # self._create_db_if_not_exists()
        # TODO: Remove this module if it's not needed

def get_default():
    return SqliteStorage(DEFAULT_PATH)
