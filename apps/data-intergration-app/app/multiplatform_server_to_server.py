import requests
from urllib3.util.retry import Retry
import simplejson as json
from flask import current_app
from app.helpers import ConfigVariableHelper
import os


class MultiplatformServerToServerSenderException(Exception):
    pass


class MultiplatformServerToServerSender:
    API_URL = '[FILL ME IN S2S ENDPOINT]'
    REQUIRED_FIELDS = ['platform', 'ad_unit_id', 'event_name', 'ad_interaction_time']
    OPTIONAL_FIELDS = ['event_time', 'install_time', 'conversions', 'value', 'value_currency']

    def __init__(self, data, api_token_env_variable, s2s_token=None):
        self.events = data
        self.api_token_env_variable = api_token_env_variable
        self.s2s_token = s2s_token

    def send(self):
        current_app.logger.info('Sending conversion events to S2S endpoint')
        session = self.retrying_http_session()

        api_token = self._get_api_token()
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }

        successes = 0
        failures = 0
        for row in self.events:
            self.to_multiplatform_s2s_event(row)
            response = session.post(self.API_URL, data=json.dumps(row), headers=headers)
            if response.ok:
                successes += 1
            else:
                failures += 1
                error_message = response.json().get('message')
                current_app.logger.error(
                        f'Failed to send S2S event! Status: {response.status_code} Msg: {error_message} '
                        f'Id:{row.get("ad_unit_id")} Date:{row.get("ad_interaction_time")}')

        current_app.logger.info(
            f'{successes}/{len(self.events)} S2S events sent successfully')
        return {'successes': successes, 'failures': failures}

    def to_multiplatform_s2s_event(self, row):
        for field in self.REQUIRED_FIELDS:
            if row.get(field) is None:
                raise Exception(f'Required field: {field}')

        multiplatform_s2s_event = {}
        for key, value in row.items():
            if key in self.OPTIONAL_FIELDS or key in self.REQUIRED_FIELDS:
                multiplatform_s2s_event[key] = value

        return multiplatform_s2s_event

    def retrying_http_session(self):
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, allowed_methods=["POST"])
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
        return session

    def _get_api_token(self):
        config_helper = ConfigVariableHelper(
            os.getenv('FLASK_ENV'),
            current_app.config.get('GOOGLE_CLOUD_PROJECT'))
        var = None
        if self.api_token_env_variable:
            var = config_helper.get_variable(self.api_token_env_variable)
        elif self.s2s_token:
            var = config_helper.decrypt(self.s2s_token)
        if var:
            return var
        else:
            raise MultiplatformServerToServerSenderException('Missing API token.')
