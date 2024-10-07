import json

import requests
from flask import current_app
from src.exceptions import ApiRequestException

API_URL = "https://icanhazdadjoke.com/"


def get_random_joke():
    headers = {"Accept": "application/json"}
    r = requests.get("https://icanhazdadjoke.com/", headers=headers)
    if not r.ok:
        raise ApiRequestException(
            "Getting joke failed",
            extra={"request_code": r.status_code, "error": r.text},
        )
    return r.json()


def create_feed(joke_amount):
    current_app.logger.info(f"Creating feed with {joke_amount} jokes.")
    feed = {"data": [get_random_joke() for _ in range(int(joke_amount))]}
    return json.dumps(feed)
