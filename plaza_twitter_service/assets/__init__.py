import os

ASSET_DIR = os.path.dirname(os.path.abspath(__file__))

def open_icon():
    return open(os.path.join(ASSET_DIR, 'twitter_logo.png'), 'rb')
