import getpass
import json
import os

from xdg import XDG_CONFIG_HOME

BRIDGE_ENDPOINT_ENV = "PLAZA_BRIDGE_ENDPOINT"
TWITTER_CONSUMER_API_TOKEN_ENV = "TWITTER_CONSUMER_API_TOKEN"
TWITTER_CONSUMER_API_TOKEN_SECRET_ENV = "TWITTER_CONSUMER_API_TOKEN_SECRET"
AUTH_TOKEN_ENV = "PLAZA_BRIDGE_AUTH_TOKEN"

BRIDGE_ENDPOINT_INDEX = "plaza_bridge_endpoint"
TWITTER_CONSUMER_API_TOKEN_INDEX = "twitter_consumer_api_token"
TWITTER_CONSUMER_API_TOKEN_SECRET_INDEX = "twitter_consumer_api_token_secret"
AUTH_TOKEN_INDEX = "plaza_authentication_token"

global directory, config_file
directory = os.path.join(XDG_CONFIG_HOME, "plaza", "bridges", "twitter")
config_file = os.path.join(directory, "config.json")


def _get_config():
    if not os.path.exists(config_file):
        return {}
    with open(config_file, "rt") as f:
        return json.load(f)


def _save_config(config):
    os.makedirs(directory, exist_ok=True)
    with open(config_file, "wt") as f:
        return json.dump(config, f)


def get_bridge_endpoint():
    # Check if the bridge endpoint is defined in an environment variable
    programaker_bridge_endpoint_env = os.getenv(BRIDGE_ENDPOINT_ENV, None)
    if programaker_bridge_endpoint_env is not None:
        return programaker_bridge_endpoint_env

    # If not, request it and save it to a file
    config = _get_config()
    if config.get(BRIDGE_ENDPOINT_INDEX, None) is None:
        config[BRIDGE_ENDPOINT_INDEX] = input("Programaker bridge endpoint: ")
        if not config[BRIDGE_ENDPOINT_INDEX]:
            raise Exception("No bridge endpoint introduced")
        _save_config(config)
    return config[BRIDGE_ENDPOINT_INDEX]


def get_twitter_token():
    # Check if the consumer api token is defined in an environment variable
    consumer_api_token_env = os.getenv(TWITTER_CONSUMER_API_TOKEN_ENV, None)
    if consumer_api_token_env is not None:
        return consumer_api_token_env

    # If not, request it and save it to a file
    config = _get_config()
    if config.get(TWITTER_CONSUMER_API_TOKEN_INDEX, None) is None:
        config[TWITTER_CONSUMER_API_TOKEN_INDEX] = input("Consumer API token: ").strip()
        if not config[TWITTER_CONSUMER_API_TOKEN_INDEX]:
            raise Exception("No consumer API token introduced")
        _save_config(config)
    return config[TWITTER_CONSUMER_API_TOKEN_INDEX]


def get_twitter_token_secret():
    # Check if the consumer api token is defined in an environment variable
    consumer_api_token_env = os.getenv(TWITTER_CONSUMER_API_TOKEN_SECRET_ENV, None)
    if consumer_api_token_env is not None:
        return consumer_api_token_env

    # If not, request it and save it to a file
    config = _get_config()
    if config.get(TWITTER_CONSUMER_API_TOKEN_SECRET_INDEX, None) is None:
        config[TWITTER_CONSUMER_API_TOKEN_SECRET_INDEX] = input(
            "Consumer API token *secret*: "
        ).strip()
        if not config[TWITTER_CONSUMER_API_TOKEN_SECRET_INDEX]:
            raise Exception("No consumer API token *secret* introduced")
        _save_config(config)
    return config[TWITTER_CONSUMER_API_TOKEN_SECRET_INDEX]


def get_auth_token():
    env_val = os.getenv(AUTH_TOKEN_ENV, None)
    if env_val is not None:
        return env_val

    config = _get_config()
    if config.get(AUTH_TOKEN_INDEX, None) is None:
        config[AUTH_TOKEN_INDEX] = input("Programaker authentication TOKEN: ")
        if not config[AUTH_TOKEN_INDEX]:
            raise Exception("No authentication token introduced")
        _save_config(config)
    return config[AUTH_TOKEN_INDEX]
