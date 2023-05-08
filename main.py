import configparser
import logging
import shutil
import sys
import time
from pathlib import Path

import Mafia
import Storage
import UI

FILENAME = time.strftime("Log%Y-%m-%d-%H:%M.log")

DEFAULT_SECTION = "DEFAULT"
DATABASE_SECTION = "Database"

LOG_LEVEL_KEY = "loglevel"
LOG_PATH_KEY = "path"
BOT_TOKEN_KEY = "token"
DATABASE_KEY = "name"
ENTITIES_KEY = "entities"


def read_config():
    config_values = {}
    config = configparser.ConfigParser()
    config.read('config.ini')
    config_values.update(**config[DEFAULT_SECTION])
    config_values.update(**config[DATABASE_SECTION])
    return config_values


def start_logging(path: str, log_level: str):
    Path(path).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=f"{path}/{FILENAME}", level=log_level, format="%(asctime)s : %(levelno)s:"
                                                                               "%(levelname)s:%(name)s : %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info("Starting Logging")


def stop_logging(path: str):
    logging.info("Ending Logging")
    logging.shutdown()
    shutil.copyfile(f"{path}/{FILENAME}", f"{path}/LATEST.log")


if __name__ == '__main__':
    config_data = read_config()
    start_logging(config_data[LOG_PATH_KEY], config_data[LOG_LEVEL_KEY])

    Storage.configure_database(config_data[DATABASE_KEY], config_data[ENTITIES_KEY])
    Mafia.register_mafia_components()
    world = Mafia.setup_world()
    UI.setup_bot()
    UI.start_bot(config_data["token"])

    stop_logging(config_data[LOG_PATH_KEY])
