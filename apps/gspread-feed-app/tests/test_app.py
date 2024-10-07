import base64

import pytest
from argon2 import PasswordHasher
from flask import Response
from gspread import SpreadsheetNotFound
from app import create_app

ph = PasswordHasher()
hashed_password = ph.hash("l3th4l")
MOCK_USERS = {
    "spreadsheet1": hashed_password,
    "spreadsheet2": hashed_password,
    "wrong_spreadsheet": hashed_password,
}

ph = PasswordHasher()
hashed_password = ph.hash("l3th4l")
MOCK_USERS = {
    "spreadsheet1": hashed_password,
    "spreadsheet2": hashed_password,
    "wrong_spreadsheet": hashed_password,
}

MOCK_CONFIG = {
    "spreadsheet_no_match": "feed",
}


class MyResponse(Response):
    """Implements custom deserialization method for response objects."""

    @property
    def json(self):
        """What is the meaning of life, the universe and everything?"""
        return self.data


class MockedCredentialsObject(object):
    @staticmethod
    def from_service_account_info(v, **kwargs):
        return "invalid info"


class MockedWorksheet(object):
    @staticmethod
    def get_all_values():
        return [["header1", "header2"], ["value1", "value2"]]


class MockedGspreadClient(object):
    @staticmethod
    def open_by_key(spreadsheet_value):
        if spreadsheet_value == "wrong_spreadsheet":
            raise SpreadsheetNotFound
        else:
            return MockedSpreadsheet

    @staticmethod
    def authorize():
        return MockedGspreadClient


class MockedSpreadsheet(object):
    @staticmethod
    def get_worksheet(worksheet_number):
        return MockedWorksheet


def mocked_gpsread_authorize(credentials):
    return MockedGspreadClient


@pytest.fixture
def app():
    app = create_app()
    app.response_class = MyResponse
    return app


def test_health_check(client):
    response = client.get("/health")
    assert b"OK" in response.data


def test_incorrect_user_credentials_provided(client, mocker):
    mocker.patch("app.get_users", return_value=MOCK_USERS)
    mocker.patch("app.get_credentials", MockedCredentialsObject)
    mocker.patch("app.get_worksheets_config", return_value=MOCK_CONFIG)
    userAndPass = base64.b64encode(b"user1:wrong_password").decode("ascii")
    headers = {"Authorization": "Basic %s" % userAndPass}
    response = client.get("/?spreadsheet=spreadsheet1", headers=headers)
    assert "403" in response.status
    assert "Failed to authenticate" in str(response.json)


def test_incorrect_spreadsheet_id_provided(client, mocker):
    mocker.patch("app.get_users", return_value=MOCK_USERS)
    mocker.patch("app.get_credentials", MockedCredentialsObject)
    mocker.patch("app.get_worksheets_config", return_value=MOCK_CONFIG)
    mocker.patch("gspread.authorize", mocked_gpsread_authorize)
    userAndPass = base64.b64encode(b"user1:l3th4l").decode("ascii")
    headers = {"Authorization": "Basic %s" % userAndPass}
    response = client.get("/?spreadsheet=wrong_spreadsheet", headers=headers)
    assert "404" in response.status
    assert "The spreadsheet was not found" in str(response.json)


def test_successfully_authenticated_and_spreadhseet_found(client, mocker):
    mocker.patch("app.get_users", return_value=MOCK_USERS)
    mocker.patch("app.get_credentials", MockedCredentialsObject)
    mocker.patch("app.get_worksheets_config", return_value=MOCK_CONFIG)
    mocker.patch("gspread.authorize", mocked_gpsread_authorize)
    userAndPass = base64.b64encode(b"user1:l3th4l").decode("ascii")
    headers = {"Authorization": "Basic %s" % userAndPass}
    response = client.get("/?spreadsheet=spreadsheet1", headers=headers)
    assert "200" in response.status
    assert "Content-Disposition: attachment; filename=export.csv" in str(
        response.headers
    )
    assert "b'header1,header2\\r\\nvalue1,value2\\r\\n'" in str(response.json)


def test_user_credentials_not_provided(client, mocker):
    response = client.get("/?spreadsheet=spreadsheet1")
    assert "401" in response.status
    assert "Access Denied" in str(response.json)


def test_spreadsheet_not_provided(client, mocker):
    response = client.get("/")
    assert "400" in response.status
    assert "Spreadsheet id parameter is missing" in str(response.json)
