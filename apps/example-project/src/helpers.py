import os
import logging
import sys
import hashlib
import copy
from urllib.parse import urlparse, parse_qs
from uuid import uuid4

from flask import request
from flask.logging import default_handler
from pythonjsonlogger import jsonlogger


# Configuration based on the OWASP cheat sheet
# https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html


ITERATIONS = 120000
ALGORITHM = "sha512"
ENCODING = "utf-8"
ALLOWED_DIGITS = 3
REQUEST_ID_HEADER = "x-request-id"
APP_SECRET = os.getenv("APP_SECRET")


def hash_secret(secret: str) -> str:
    if not secret:
        raise ValueError("Empty secret not allowed.")
    hashed = hashlib.pbkdf2_hmac(
        ALGORITHM, secret.encode(ENCODING), APP_SECRET.encode(ENCODING), ITERATIONS
    )
    return hashed.hex()


class Obfuscator:

    # Update this list if you have additional secrets in request header or query parameters
    FIELDS_TO_OBFUSCATE = [
        "appsecretproof",
        "accesstoken",
        "password",
        "token",
        "secret",
        "authorization",
        "cookie",
    ]

    @staticmethod
    def _obfuscate_str(secret) -> str:
        try:
            return f"{hash_secret(str(secret))} (OBFUSCATED)"
        except Exception:
            return "Logger Error(OBFUSCATED)"

    @staticmethod
    def _obfuscate_str_in_path(secret) -> str:
        return "*" * (len(secret) - ALLOWED_DIGITS) + secret[-ALLOWED_DIGITS:]

    @classmethod
    def get_cleaned_record(cls, log_record: dict) -> dict:
        def modify_all_dirty_flat_pairs(nested: dict):
            for key, value in nested.items():
                if isinstance(value, dict):
                    modify_all_dirty_flat_pairs(value)
                elif key.lower() in cls.FIELDS_TO_OBFUSCATE:
                    nested[key] = cls._obfuscate_str(value)

        cleaned_record = copy.deepcopy(log_record)
        modify_all_dirty_flat_pairs(cleaned_record)
        return cleaned_record

    @classmethod
    def get_cleaned_path(cls, path: str) -> str:
        query_string = urlparse(path).query
        query_params = parse_qs(query_string)
        for key, values in query_params.items():
            if key.lower() in cls.FIELDS_TO_OBFUSCATE:
                for value in values:
                    path = path.replace(value, cls._obfuscate_str_in_path(value))
        return path


class StackdriverLogFormatter(jsonlogger.JsonFormatter, object):
    def __init__(self, fmt="%(levelname) %(message)", style="%", *args, **kwargs):
        jsonlogger.JsonFormatter.__init__(self, fmt=fmt, *args, **kwargs)

    def process_log_record(self, log_record):
        log_record[REQUEST_ID_HEADER] = request.id if hasattr(request, "id") else "N/A"
        log_record["severity"] = log_record["levelname"]
        del log_record["levelname"]
        log_record = Obfuscator.get_cleaned_record(log_record)
        return super(StackdriverLogFormatter, self).process_log_record(log_record)


def setup_logging(flask_app, level=logging.INFO):
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = StackdriverLogFormatter()
    log_handler.setFormatter(formatter)
    flask_app.logger.addHandler(log_handler)
    flask_app.logger.removeHandler(default_handler)
    flask_app.logger.setLevel(level)


def get_logging_details(status_code, path):
    path = Obfuscator.get_cleaned_path(path)
    extra = {
        "headers": dict(request.headers),
        "status_code": status_code,
        "path": path,
    }
    message = "REQUEST %s %s %s" % (request.method, path, status_code)
    return message, extra


def generate_request_id():
    return request.headers.get(REQUEST_ID_HEADER, uuid4().hex)
