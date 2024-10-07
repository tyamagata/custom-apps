import logging

from src.helpers import setup_logging
from src.email_csv_to_sftp import run_email_csv_to_sftp

# Setup for logger
logger = logging.getLogger(__name__)
setup_logging(logger)


def main():
    try:
        logger.info("Starting the Email CSV file to SFTP Upload application")
        run_email_csv_to_sftp()
        logger.info("Finished running the Email CSV file to SFTP Upload application")
    except Exception as e:
        logger.error("Error occurred", exc_info=e)


if __name__ == "__main__":
    main()
