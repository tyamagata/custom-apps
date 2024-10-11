from app.s3 import should_process_file
from tests.boto3_mocks import BotoObject
from datetime import datetime, timedelta


def test_validate_file():
    boto_item = BotoObject()
    unaware_timezone = datetime(2020, 8, 15, 8, 15, 12, 0)
    item = should_process_file(boto_item, unaware_timezone)
    assert bool(item) is True


def test_validate_file_content_type_is_in_correct():
    boto_item = BotoObject()
    boto_item.set_content_type("application/x-directory")
    unaware_timezone = datetime(2020, 8, 15, 8, 15, 12, 0)
    item = should_process_file(boto_item, unaware_timezone)
    assert bool(item) is False


def test_validate_file_processing_time_in_future():
    boto_item = BotoObject()
    unaware_timezone = datetime.utcnow() + timedelta(days=2)
    item = should_process_file(boto_item, unaware_timezone)
    assert bool(item) is False
