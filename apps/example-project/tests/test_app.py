import json

from mocket.mockhttp import Entry
import pytest

from app import create_app
from src import feedparser
from tests.utils import strict_mocketize


# The client fixture comes magically from the pytest-flask library
# Request mocking with Python Mocket https://github.com/mindflayer/python-mocket


@pytest.fixture  # Don't remove, used by pytest in the background
def app():
    app.testing = True
    return create_app()


def test_health_check(client):
    response = client.get("/health")
    assert b"OK" in response.data


# Example test to make sure errors in parameters are handled
def test_param_test_example(client):
    response = client.get("/param_test_example")
    assert "404 NOT FOUND" in response.status

    response = client.get("/param_test_example?param1=123")
    assert "403 FORBIDDEN" in response.status

    response = client.get("/param_test_example?param1=123&param2=456")
    assert b"OK" in response.data


# Example test using Mocket to mock away the HEAD and GET request to the Joke API
@strict_mocketize
def test_feed_endpoint_example(client):
    access_url = feedparser.API_URL
    Entry.single_register(
        Entry.HEAD,
        access_url,
    )  # status 200 is default
    api_url = feedparser.API_URL
    Entry.single_register(
        Entry.GET,
        api_url,
        body=json.dumps({}),
        headers={"content-type": "application/json"}
    )
    url = "/"
    response = client.get(url)
    assert "200" in response.status


# Example test using Mocket to get a failure response for the HEAD
@strict_mocketize
def test_feed_endpoint_failure_example(client):
    access_url = feedparser.API_URL
    Entry.single_register(
        Entry.HEAD,
        access_url,
        status=404,
    )
    url = "/"
    response = client.get(url)
    assert b"404" in response.data
