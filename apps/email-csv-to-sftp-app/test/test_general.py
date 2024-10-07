from unittest.mock import patch, MagicMock
import src.email_csv_to_sftp as script


@patch("src.email_csv_to_sftp.imaplib.IMAP4_SSL")
def test_init_mail_session(mock_imap):
    mock_mail = MagicMock()
    mock_imap.return_value = mock_mail

    script.init_mail_session()

    mock_mail.login.assert_called_with(script.GMAIL_USERNAME, script.GMAIL_PASSWORD)


@patch("src.email_csv_to_sftp.imaplib.IMAP4_SSL")
def test_fetch_unread_emails(mock_imap):
    # Setup mock
    mock_mail = MagicMock()
    mock_imap.return_value = mock_mail
    mock_mail.search.return_value = ("OK", [b"1 2 3"])

    # Create a mock mail session using the patched imaplib.IMAP4_SSL
    mail = script.init_mail_session()
    email_ids = script.fetch_unread_emails(mail, "TestLabel")
    assert email_ids == [b"1", b"2", b"3"]
    mock_mail.search.assert_called_with(None, "UNSEEN")


@patch("src.email_csv_to_sftp.paramiko.SFTPClient.from_transport")
@patch("src.email_csv_to_sftp.paramiko.Transport")
def test_upload_to_sftp(mock_transport_class, mock_from_transport):
    # Setup mock for SFTPClient
    mock_sftp_client = MagicMock()
    mock_from_transport.return_value = mock_sftp_client

    # Mock the Transport class to prevent actual network connections
    mock_transport_instance = MagicMock()
    mock_transport_class.return_value = mock_transport_instance

    # Prepare dummy file for upload
    filepath = "/tmp/testfile.csv"
    with open(filepath, "w") as f:
        f.write("test data")

    # Customer config
    customer = {
        "sftp_host": "test_host",
        "sftp_port": 22,
        "sftp_username": "test_user",
        "sftp_password": "test_pass",
        "sftp_directory": "/test_dir",
        "customer_name": "Test Customer",
    }

    # Execute test
    script.upload_to_sftp(filepath, "testfile.csv", customer)

    # Verify the SFTP client's put method was called with the correct arguments
    mock_sftp_client.put.assert_called_with(filepath, "testfile.csv")
