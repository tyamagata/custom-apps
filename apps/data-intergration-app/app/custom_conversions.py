import requests
import os
import math
from flask import current_app
import simplejson as json
from app.helpers import ConfigVariableHelper


class CustomConversionSenderException(Exception):
    pass


class CustomConversionSender:
    API_URL = '[FILL ME IN S2S ENDPOINT]'

    def __init__(self, data, api_token_env_variable):
        self.data = data
        self.api_token_env_variable = api_token_env_variable

    @staticmethod
    def chunks(data, chunk_size):
        for i in range(0, chunk_size):
            yield data[i::chunk_size]

    def get_chunk_size(self):
        if len(self.data) <= 10000:
            return 1
        else:
            return math.ceil(len(self.data) / 10000)

    def _generate_api_payloads(self):
        payloads = []

        for chunk in self.chunks(self.data, self.get_chunk_size()):
            payload = {
                'ignore_invalid_ad_ids': True,
                'data': []
            }
            for row in chunk:
                payload['data'].append(row)
            payloads.append(payload)

        return payloads

    def _get_api_token(self):
        config_helper = ConfigVariableHelper(
            os.getenv('FLASK_ENV'),
            current_app.config.get('GOOGLE_CLOUD_PROJECT'))

        var = config_helper.get_variable(self.api_token_env_variable)
        if var:
            return var
        else:
            raise CustomConversionSenderException('Missing API token from ENV')

    @staticmethod
    def _rows_in_payload(payload):
        return len(payload['data'])

    def send(self):
        if len(self.data) > 0:
            current_app.logger.info(
                'Sending conversion events to custom conversion import API')
            payloads = self._generate_api_payloads()
            api_token = self._get_api_token()

            headers = {
                'Authorization': api_token,
                'Content-Type': 'application/json'
            }

            responses = []
            for payload in payloads:
                response = requests.post(
                    self.API_URL,
                    data=json.dumps(payload),
                    headers=headers)
                response.raise_for_status()
                response_data = response.json()
                responses.append({
                    'successes': response_data.get('count'),
                    'failures': self._rows_in_payload(payload) - response_data.get('count')
                })
            total_successes = sum([r['successes'] for r in responses])
            total_failures = sum([r['failures'] for r in responses])

            return {
                'successes': total_successes,
                'failures': total_failures
            }
        else:
            current_app.logger.info('No data to send to custom conversion import API')
            return {'successes': 0, 'failures': 0}
