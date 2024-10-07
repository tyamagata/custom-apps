from src.helpers import get_credentials

google_service_account_credentials = {
    "type": "service_account",
    "project_id": "custom-apps-tc",
    "private_key_id": get_credentials("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": get_credentials("GOOGLE_PRIVATE_KEY"),
    "client_email": "custom-apps-tc@custom-apps-tc.iam.gserviceaccount.com",
    "client_id": get_credentials("GOOGLE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": (
        "https://www.googleapis.com/robot/v1/metadata/x509/"
        "custom-apps-tc%40custom-apps-tc.iam.gserviceaccount.com"
    ),
    "universe_domain": "googleapis.com",
}

# Customer specific configurations add new dictionary for new customers.
CUSTOMERS = [
    {
        "customer_name": "Zillow Workspaces Feed to Google Sheet",
        "sftp": {
            "host": "feedup.smartly.io",
            "username": get_credentials("ZILLOW_SFTP_USERNAME"),
            "password": get_credentials("ZILLOW_SFTP_PASSWORD"),
            "file_path": "/smartly_feeds/smartlyFacebookMFBoost.csv",
        },
        "google_sheets": {
            "sheet_id": "1oRHlTi4GxwsSHllTR57Ya2QjeGsA65LjWmQxK0bs-Ag",
            "tab_name": "SFTP File",
        },
    },
    {
        "customer_name": "Zillow Builder Feed to Google Sheet",
        "sftp": {
            "host": "feedup.smartly.io",
            "username": get_credentials("ZILLOW_SFTP_USERNAME"),
            "password": get_credentials("ZILLOW_SFTP_PASSWORD"),
            "file_path": "/buildermedia.csv",
        },
        "google_sheets": {
            "sheet_id": "1fAoIH5RGmzUGnMJ673RRbFQtAq2CEzyySU3ymgHBZhc",
            "tab_name": "SFTP File",
        },
    },
]
