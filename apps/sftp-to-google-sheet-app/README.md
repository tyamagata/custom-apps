# SFTP to Google Sheets Uploader

This project provides a Python script for automating the process of downloading CSV files from an SFTP server and uploading their content to specified Google Sheets.

## Features

- Connects to an SFTP server to download CSV files.
- Clears the Data from the Google Sheet.
- Uploads CSV content directly into a specified Google Sheet and tab.
- Supports multiple customer configurations through a single execution.
- Runs on a 12 hour cadence.

## Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- Access to an SFTP server
- Google Cloud Platform project with the Sheets API enabled
- Service account with permissions to access the desired Google Sheets

## Installation

1. **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd sftp_google_sheet_upload
    ```

2. **Set up a virtual environment** (optional but recommended):

    ```bash
    python3 -m venv myenv
    source myenv/bin/activate
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure the application**:

    Create a new CUSTOMER array in the `config.py` file in the root directory with your SFTP and Google Sheets configuration.

    This should include a SFTP Username, Password and file. As well as, a Google sheet ID and tab name.

    In the Google Sheet, you will need to add Google Cloud email to the Google Sheet you will upload data to `custom-apps-tc@custom-apps-tc.iam.gserviceaccount.com`.

## Usage

Ensure your virtual environment is activated and run the script:

```bash
python sftp_google_sheet_upload.py
