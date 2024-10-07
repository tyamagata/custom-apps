import logging
import sys
import os
import json

from pythonjsonlogger import jsonlogger

secrets_path_credentials = os.getenv("SECRETS_PATH_CREDENTIALS", "")


class StackdriverLogFormatter(jsonlogger.JsonFormatter, object):
    def __init__(self, fmt="%(levelname) %(message)", style="%", *args, **kwargs):
        jsonlogger.JsonFormatter.__init__(self, fmt=fmt, *args, **kwargs)

    def process_log_record(self, log_record):
        log_record["severity"] = log_record["levelname"]
        del log_record["levelname"]
        return super(StackdriverLogFormatter, self).process_log_record(log_record)


def setup_logging(logger, level=logging.INFO):
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = StackdriverLogFormatter()
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(level)


def get_credentials(key: str):
    if not os.path.exists(secrets_path_credentials):
        return None

    with open(secrets_path_credentials, "r") as f:
        credentials = json.load(f)
    return credentials[key]
