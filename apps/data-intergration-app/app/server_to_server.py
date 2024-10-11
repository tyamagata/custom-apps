import requests
from flask import current_app


class ServerToServerSenderException(Exception):
    pass


class ServerToServerSender:
    API_URL = '[FILL ME IN S2S ENDPOINT]'

    def __init__(self, data):
        self.data = data

    def send(self):
        current_app.logger.info('Sending conversion events to S2S endpoint')
        session = self.retrying_http_session()

        successes = 0
        failures = 0
        for row in self.data:
            response = session.get(self.API_URL, params=self.to_s2s_event(row))
            if response is not None and response.status_code == requests.codes.ok:
                successes += 1
            else:
                if response is None:
                    current_app.logger.error(
                        'Failed to send S2S event! No response')
                else:
                    current_app.logger.error(
                        'Failed to send S2S event! Status: {}'.format(
                            response.status_code))
                failures += 1

        current_app.logger.info(
            '{}/{} S2S events sent successfully'.format(successes, len(self.data)))
        return {'successes': successes, 'failures': failures}

    def to_s2s_event(self, row):
        return {
            'type': 's2s',
            'fb_ad_id': row['ad_id'],
            'event_name': row['type'],
            'fb_click_time': row.get('fb_click_time'),
            'event_time': row.get('event_time'),
            'install_time': row.get('install_time'),
            'actions': row.get('actions'),
            'revenue': row.get('value')
        }

    def retrying_http_session(self):
        session = requests.Session()
        session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        return session
