from src.helpers import get_credentials

# Gmail credentials (common for all customers)
GMAIL_USERNAME = get_credentials("EMAIL_USERNAME")
GMAIL_PASSWORD = get_credentials("EMAIL_PASSWORD")
GMAIL_IMAP_URL = "imap.gmail.com"

# Customer specific configurations
CUSTOMERS = [
    {
        "customer_name": "Saks - Visits",
        "label": "Adobe Analytics/Saks - Visits",
        "from_email": "no-reply@adobe.com",
        "subject_keyword": "Saks x Smartly Daily Report",
        "sftp_host": "feedup.smartly.io",
        "sftp_port": 22,
        "sftp_username": get_credentials("SAKS_SFTP_USERNAME"),
        "sftp_password": get_credentials("SAKS_SFTP_PASSWORD"),
        "sftp_directory": "/custom_conversion_api/Saks/Visits",
    },
    {
        "customer_name": "Saks - Orders",
        "label": "Adobe Analytics/Saks - Orders",
        "from_email": "no-reply@adobe.com",
        "subject_keyword": "Saks x Smartly Daily Report",
        "sftp_host": "feedup.smartly.io",
        "sftp_port": 22,
        "sftp_username": get_credentials("SAKS_SFTP_USERNAME"),
        "sftp_password": get_credentials("SAKS_SFTP_PASSWORD"),
        "sftp_directory": "/custom_conversion_api/Saks/Orders",
    },
    {
        "customer_name": "Saks - Coop",
        "label": "Adobe Analytics/Saks - Coop",
        "from_email": "no-reply@omniture.com",
        "subject_keyword": "SAKS COOP_SMARTLY_DAILY REPORT",
        "sftp_host": "feedup.smartly.io",
        "sftp_port": 22,
        "sftp_username": get_credentials("SAKS_SFTP_USERNAME"),
        "sftp_password": get_credentials("SAKS_SFTP_PASSWORD"),
        "sftp_directory": "/custom_conversion_api/Saks/Coop",
    },
    {
        "customer_name": "Tommy",
        "label": "Adobe Analytics/Tommy Hilfiger",
        "from_email": "no-reply@adobe.com",
        "subject_keyword": "Adobe Social Data TH",
        "sftp_host": "feedup.smartly.io",
        "sftp_port": 22,
        "sftp_username": get_credentials("TOMMY_SFTP_USERNAME"),
        "sftp_password": get_credentials("TOMMY_SFTP_PASSWORD"),
        "sftp_directory": "/s2s_data",
    }
    # Add more customer dictionaries as needed
]
