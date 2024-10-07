import imaplib
import email
import os
import paramiko
import tempfile
from src.config import GMAIL_USERNAME, GMAIL_PASSWORD, GMAIL_IMAP_URL, CUSTOMERS


def valid_msg(part):
    return (
        part.get_content_maintype() != "multipart"
        and part.get("Content-Disposition") is not None
    )


def valid_file(filename):
    return filename and filename.endswith(".csv")


def init_mail_session():
    mail = imaplib.IMAP4_SSL(GMAIL_IMAP_URL)
    mail.login(GMAIL_USERNAME, GMAIL_PASSWORD)
    return mail


def fetch_unread_emails(mail, label):
    mail.select(f'"{label}"')
    type, data = mail.search(None, "UNSEEN")
    return data[0].split()


def download_attachment(part, customer):
    filename = part.get_filename()
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".csv", mode="wb", dir="/tmp"
    ) as temp_file:
        temp_file.write(part.get_payload(decode=True))
        filepath = temp_file.name
        print(f"Downloaded CSV attachment: {filename} for {customer['customer_name']}")
    return filepath, filename


def upload_to_sftp(filepath, filename, customer):
    sftp_host = customer["sftp_host"]
    sftp_port = customer["sftp_port"]
    sftp_username = customer["sftp_username"]
    sftp_password = customer["sftp_password"]
    sftp_directory = customer["sftp_directory"]

    transport = paramiko.Transport((sftp_host, sftp_port))
    transport.connect(username=sftp_username, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        sftp.chdir(sftp_directory)
    except IOError:
        sftp.mkdir(sftp_directory)
        sftp.chdir(sftp_directory)
    sftp.put(filepath, filename)
    sftp.close()
    transport.close()
    print(f"Uploaded {filename} to SFTP successfully for {customer['customer_name']}.")


def process_emails_for_customer(mail, customer):
    email_ids = fetch_unread_emails(mail, customer["label"])

    if not email_ids or email_ids[0] == b"":
        print(f"No matching unread emails found for {customer['customer_name']}.")
        return None

    for email_id in email_ids:
        typ, message_data = mail.fetch(email_id, "(RFC822)")
        for response_part in message_data:
            if not isinstance(response_part, tuple):
                continue

            msg = email.message_from_bytes(response_part[1])
            for part in msg.walk():
                if not valid_msg(part):
                    continue

                filename = part.get_filename()
                if not valid_file(filename):
                    continue

                filepath, original_filename = download_attachment(part, customer)
                try:
                    upload_to_sftp(filepath, original_filename, customer)
                    os.remove(filepath)
                    mail.store(email_id, "+FLAGS", "\\Seen")
                except Exception as e:
                    print(
                        f"Failed to upload {original_filename} to SFTP "
                        f"for {customer['customer_name']}. Error: {e}"
                    )
                    os.remove(filepath)


def run_email_csv_to_sftp():
    mail = init_mail_session()

    for customer in CUSTOMERS:
        process_emails_for_customer(mail, customer)

    mail.logout()
