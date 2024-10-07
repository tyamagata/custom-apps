import pytest
from unittest.mock import patch, MagicMock, ANY
import os
import tempfile  # noqa: F401
from src.sftp_to_google_sheet import (
    download_sftp_file,
    upload_to_google_sheet_in_batches,
)


@pytest.fixture
def sftp_config():
    """Fixture to provide fake SFTP configuration."""
    return {
        "host": "fakehost.com",
        "username": "fakeuser",
        "password": "fakepass",
        "file_path": "/path/to/fakefile.csv",
    }


@pytest.fixture
def customer_config():
    """Fixture to provide fake Google Sheets configuration."""
    return {
        "google_sheets": {
            "sheet_id": "fake_sheet_id",
            "tab_name": "Sheet1",
        }
    }


# Mock the Google Sheets client
@pytest.fixture
def gclient_mock():
    """Fixture to create a mock Google Sheets client."""
    gclient = MagicMock()
    gclient.open_by_key.return_value.worksheet.return_value.clear.return_value = True
    gclient.open_by_key.return_value.worksheet.return_value.update.return_value = True
    return gclient


@patch("src.sftp_to_google_sheet.paramiko.SFTPClient.from_transport")
@patch("src.sftp_to_google_sheet.paramiko.Transport")
def test_download_sftp_file(mock_transport, mock_from_transport, sftp_config):
    mock_sftp_client = MagicMock()
    mock_from_transport.return_value = mock_sftp_client

    mock_sftp_client.get = MagicMock()

    local_filepath = download_sftp_file(sftp_config)  # noqa: F841

    mock_transport.assert_called_with((sftp_config["host"], 22))
    mock_transport.return_value.connect.assert_called_with(
        username=sftp_config["username"], password=sftp_config["password"]
    )
    mock_from_transport.assert_called_once()

    filename = sftp_config["file_path"].split("/")[-1]
    mock_sftp_client.get.assert_called_with(filename, ANY)


@patch("src.sftp_to_google_sheet.gspread.authorize")
def test_upload_to_google_sheet_in_batches(
    mock_authorize, customer_config, gclient_mock, tmpdir
):
    mock_authorize.return_value = gclient_mock

    temp_file = tmpdir.join("temporary_file.csv")
    temp_file.write(
        "col1,col2\nvalue1,value2\nvalue3,value3\nvalue4,value4\nvalue5,value5\n"
    )

    assert os.path.exists(temp_file)

    upload_to_google_sheet_in_batches(
        gclient_mock, customer_config, str(temp_file), batch_size=2
    )

    gclient_mock.open_by_key.assert_called_once_with(
        customer_config["google_sheets"]["sheet_id"]
    )
    sheet = gclient_mock.open_by_key().worksheet()
    sheet.clear.assert_called_once()
    sheet.update.assert_any_call("A1", [["col1", "col2"]])
    sheet.update.assert_any_call("A2", [["value1", "value2"], ["value3", "value3"]])
    sheet.update.assert_any_call("A4", [["value4", "value4"], ["value5", "value5"]])

    if os.path.exists(str(temp_file)):
        os.remove(str(temp_file))
