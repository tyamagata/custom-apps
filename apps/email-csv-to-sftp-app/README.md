# Email CSV to SFTP File Upload

This application automates the process of fetching emails with CSV attachments from a specified Gmail account, downloading those attachments, and uploading them to an SFTP server. It's designed to streamline workflows that involve regular data transfer from email to secure file servers, making it highly valuable for businesses that rely on automated data processing and distribution.

## Description

The **Email CSV to SFTP File Upload** app leverages Python to interact with Gmail for fetching emails, parsing attachments, and handling file uploads to an SFTP server based on predefined customer configurations. This solution is particularly useful for managing data feeds, automating report deliveries, or any scenario where CSV data needs to be regularly extracted from emails and securely stored or processed.

### Key Features

- **Automated Email Fetching**: Connects to a Gmail account to fetch unread emails with specific labels.
- **CSV Attachment Processing**: Downloads CSV file attachments and prepares them for upload.
- **Secure File Transfer**: Uploads the CSV files to designated SFTP servers based on customer-specific configurations.
- **Configurable**: Allows for easy setup for multiple customers, each with their own SFTP destinations and email criteria.

## Setup and Configuration

### Dependencies

Ensure the following dependencies are installed in your environment:

- Python 3.x
- `pandas` for data handling (if data manipulation is required).
- `paramiko` for SFTP operations.
- Other dependencies as listed in `requirements.txt`.

### Installation

1. Clone the repository to your local machine.
2. Set up a virtual environment:
   ```bash
   python3 -m venv env
   source env/bin/activate  # On Unix/macOS
   .\env\Scripts\activate  # On Windows
