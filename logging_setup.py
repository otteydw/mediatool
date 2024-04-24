import json
import logging.config


def logging_setup():
    with open("logging.json", "r") as f:
        config = json.load(f)
        logging.config.dictConfig(config)
