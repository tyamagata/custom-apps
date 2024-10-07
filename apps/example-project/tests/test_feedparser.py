import json

from mocket.mockhttp import Entry
import pytest

from app import create_app
from src import feedparser, exceptions
from tests.utils import strict_mocketize

# Setup for preventing current_app.logger from causing errors
ctx = create_app().app_context()
ctx.push()


@pytest.fixture
def example_joke():
    with open("tests/fixtures/example_joke.json", "r") as f:
        return json.load(f)


@pytest.fixture
def example_feed():
    with open("tests/fixtures/example_feed.json", "r") as f:
        return json.load(f)


def mock_get_random_joke():
    with open("tests/fixtures/example_joke.json", "r") as f:
        return json.load(f)


# Example for testing feed creation, mocking away the entire get_random_joke function
@strict_mocketize
def test_get_random_joke(example_joke):
    # Works as expected if simply returns the entire joke
    Entry.single_register(
        Entry.GET,
        feedparser.API_URL,
        body=json.dumps(example_joke),
        headers={"content-type": "application/json"}
    )
    assert feedparser.get_random_joke() == example_joke


# Example for testing error raising when not getting ok response
@strict_mocketize
def test_jokes_api_500():
    # Jokes API not OK
    Entry.single_register(
        Entry.GET,
        feedparser.API_URL,
        status=500
    )
    with pytest.raises(exceptions.ApiRequestException):
        assert feedparser.get_random_joke()


# Example for testing feed creation, mocking away the entire get_random_joke function
def test_create_feed(mocker, example_feed):
    mocker.patch("src.feedparser.get_random_joke", mock_get_random_joke)
    feed = feedparser.create_feed(5)
    assert feed == json.dumps(example_feed)
