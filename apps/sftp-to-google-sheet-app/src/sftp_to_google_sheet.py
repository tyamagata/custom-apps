import paramiko
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import os
import tempfile
from src.config import google_service_account_credentials, CUSTOMERS


# Initialize Google Sheets client
def authenticate_google_sheets_with_service_account():
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        google_service_account_credentials
    )
    return gspread.authorize(credentials)


def download_sftp_file(sftp_config):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        local_filepath = temp_file.name
        transport = paramiko.Transport((sftp_config["host"], 22))
        transport.connect(
            username=sftp_config["username"], password=sftp_config["password"]
        )
        sftp = paramiko.SFTPClient.from_transport(transport)

        directory, filename = os.path.split(sftp_config["file_path"])
        if directory:
            sftp.chdir(directory)

        sftp.get(filename, local_filepath)
        print(f"Downloaded {filename} to {local_filepath}")

        sftp.close()
        transport.close()

    return local_filepath


def upload_to_google_sheet_in_batches(
    gclient, customer_config, filepath, batch_size=1000
):
    sheet = gclient.open_by_key(customer_config["google_sheets"]["sheet_id"]).worksheet(
        customer_config["google_sheets"]["tab_name"]
    )
    sheet.clear()  # Clear the entire sheet

    with open(filepath, "r") as file_obj:
        csv_reader = csv.reader(file_obj)
        headers = next(csv_reader)  # Get the header row
        rows = list(csv_reader)

    # Upload headers first
    sheet.update("A1", [headers])

    total_rows = len(rows)
    total_updated_cells = 0

    # Start the data upload from 'A2' in the Google Sheet
    for start in range(0, total_rows, batch_size):
        end = min(start + batch_size, total_rows)
        batch = rows[start:end]

        # For the first batch, the range_name should start from 'A2'
        # For subsequent batches, it should continue from the row after the previous batch ended
        range_name = "A2" if start == 0 else f"A{start + 2}"

        sheet.update(range_name, batch)
        updated_cells = len(batch) * len(
            batch[0]
        )  # Assuming all rows have the same number of columns
        total_updated_cells += updated_cells
        print(f"Updated rows {start + 2} to {end + 1}, cells updated: {updated_cells}")

    print(f"Total {total_rows} rows, {total_updated_cells} cells updated.")

    # Check if the file exists before attempting to delete it
    if os.path.exists(filepath):
        os.remove(filepath)


def run_sftp_to_google_sheet():
    gclient = authenticate_google_sheets_with_service_account()
    for customer in CUSTOMERS:
        print(f"Processing {customer['customer_name']}...")
        local_filepath = download_sftp_file(customer["sftp"])
        upload_to_google_sheet_in_batches(gclient, customer, local_filepath)
