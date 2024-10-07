import logging

from src.helpers import setup_logging
from src.sftp_to_google_sheet import run_sftp_to_google_sheet

# Setup for logger
logger = logging.getLogger(__name__)
setup_logging(logger)


def main():
    try:
        logger.info("Starting the SFTP CSV file to Google Sheet Upload application")
        run_sftp_to_google_sheet()
        logger.info(
            "Finished running the SFTP CSV file to Google Sheet Upload application"
        )
    except Exception as e:
        logger.error("Error occurred", exc_info=e)


if __name__ == "__main__":
    main()
