import csv
import os
import hashlib
import base64

import cchardet as chardet
from pythonjsonlogger import jsonlogger
from google.cloud import kms_v1
from flask import current_app
from google.api_core.exceptions import InvalidArgument

CURRENT_PROCESSING_CONFIG = 'CURRENT_PROCESSING_CONFIG'


def detect_encoding(data):
    encoding = chardet.detect(data)['encoding']
    current_app.logger.info('Detected encoding {}'.format(encoding))
    return encoding


def get_csv_reader(data):
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(data[0])
    return csv.DictReader(data, dialect=dialect)


def bytesio_md5(data):
    m = hashlib.md5(data)
    return m.hexdigest()


class ConfigVariableHelper:
    def __init__(self, environment, google_project_id):
        self.environment = environment
        self.google_project_id = google_project_id
        self.kms_key_name = None
        self.kms_client = None

    def _encrypt(self, plain_text):
        client = kms_v1.KeyManagementServiceClient(
            ) if not self.kms_client else self.kms_client
        kms_key_name = client.crypto_key_path(
            self.google_project_id,
            'europe-west1',
            'config-keys',
            'master-key'
        ) if not self.kms_key_name else self.kms_key_name
        response = client.encrypt(kms_key_name, plain_text.rstrip().encode())
        return base64.b64encode(response.ciphertext).decode()

    def _decrypt(self, ciphertext):
        client = kms_v1.KeyManagementServiceClient(
            ) if not self.kms_client else self.kms_client
        ciphertext = base64.b64decode(ciphertext)
        kms_key_name = client.crypto_key_path(
            self.google_project_id,
            'europe-west1',
            'config-keys',
            'master-key'
        ) if not self.kms_key_name else self.kms_key_name
        response = client.decrypt(kms_key_name, ciphertext)
        return response.plaintext.decode().rstrip()

    def decrypt(self, token):
        if self.environment == 'production':
            return self._decrypt(token)
        else:
            if "encrypted" in token:
                return f'{token.replace("encrypted_", "")}'
            else:
                raise InvalidArgument("Couldn't decrypt token")

    def encrypt(self, token):
        if self.environment == 'production':
            return self._encrypt(token)
        else:
            return f'encrypted_{token}'

    def get_variable(self, variable_key):
        if self.environment == 'production':
            ciphertext = os.getenv(variable_key)
            if not ciphertext:
                raise Exception(
                    'Requested env variable {} does not exist'.format(variable_key))
            return self._decrypt(ciphertext)
        else:
            return os.getenv(variable_key)


class StackdriverLogFormatter(jsonlogger.JsonFormatter, object):
    def __init__(self, fmt="%(levelname) %(message)", style='%', *args, **kwargs):
        jsonlogger.JsonFormatter.__init__(self, fmt=fmt, *args, **kwargs)

    def process_log_record(self, log_record):
        log_record['severity'] = log_record['levelname']
        del log_record['levelname']
        log_record['processing_config'] = current_app.config.get(CURRENT_PROCESSING_CONFIG)
        return super(StackdriverLogFormatter, self).process_log_record(log_record)
