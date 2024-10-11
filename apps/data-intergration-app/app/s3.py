import boto3
import gzip
import os
from app.helpers import ConfigVariableHelper, bytesio_md5, detect_encoding
from flask import current_app
from io import BytesIO
from app.helpers import get_csv_reader
from pytz import UTC


def download_file_from_s3(bucket, item_key):
    file_object = BytesIO()
    bucket.download_fileobj(item_key, file_object)
    return file_object


def get_reader_from_bytes(bts, item_key):
    data = bts.getvalue()
    if len(data) > 0:
        encoding = detect_encoding(data)
        md5 = bytesio_md5(data)
        csv_data = data.decode(encoding).splitlines()
        return (get_csv_reader(csv_data), md5, item_key)
    else:
        current_app.logger.info('Empty file: {}'.format(item_key))
        return None


def get_csv_reader_from_s3(bucket, item_key):
    current_app.logger.info('Starting to fetch file {}'.format(item_key))
    file_object = download_file_from_s3(bucket, item_key)
    if item_key.endswith('.gz'):
        try:
            file_object = BytesIO(gzip.decompress(file_object.getvalue()))
        except OSError as error:
            current_app.logger.info(f'Attempted decompressing invalid gzip: {item_key}')
            raise error
    current_app.logger.info('Got file {}'.format(item_key))
    return get_reader_from_bytes(file_object, item_key)


def should_process_file(item, last_successfully_processed_at):
    if "application/x-directory" not in item.get()[
        "ContentType"
    ] and item.last_modified > UTC.localize(last_successfully_processed_at):
        return True
    return False


def get_latest_file_from_s3(
    bucket_name, path, aws_creds, last_successfully_processed_at
):
    # currently, path includes "/" - Which if included in the filter would not find the correct file.
    path = path[1:] if path[0] == '/' else path
    api_id, api_key = aws_creds.split(":")
    config_helper = ConfigVariableHelper(
        os.getenv("FLASK_ENV"), current_app.config.get("GOOGLE_CLOUD_PROJECT")
    )
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=config_helper.get_variable(api_id),
        aws_secret_access_key=config_helper.get_variable(api_key),
    )
    bucket = s3.Bucket(bucket_name)
    csv_readers = []
    for item in bucket.objects.filter(Prefix=path):
        if should_process_file(item, last_successfully_processed_at):
            csv_readers.append(get_csv_reader_from_s3(bucket, item.key))
    output = list(filter(None, csv_readers))
    return output
