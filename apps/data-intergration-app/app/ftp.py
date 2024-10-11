import pysftp
import io
import os
import calendar
import gzip
from app.helpers import get_csv_reader, bytesio_md5, detect_encoding
from flask import current_app
from ftplib import FTP
from dateutil import parser
from datetime import datetime


def get_reader_from_bytes(bts, filename):
    data = bts.getvalue()
    if len(data) > 0:
        encoding = detect_encoding(data)
        md5 = bytesio_md5(data)
        csv_data = data.decode(encoding).splitlines()
        return (get_csv_reader(csv_data), md5, filename)
    else:
        current_app.logger.info('Empty file: {}'.format(filename))
        return None


def get_reader_from_sftp(connection, file_name):
    current_app.logger.info('Starting fo fetch file {}'.format(file_name))
    bts = io.BytesIO()
    connection.getfo(file_name, bts)
    if file_name.endswith('.gz'):
        try:
            bts = io.BytesIO(gzip.decompress(bts.getvalue()))
        except OSError:
            current_app.logger.info(f'Attempted decompressing invalid gzip: {file_name}')
    current_app.logger.info('Got file {}'.format(file_name))
    return get_reader_from_bytes(bts, file_name)


def file_should_be_downloaded(filename, timestamp, last_successful_sync):
    current_app.logger.info(
                '{}, mtime={}, last_successful_sync={}'.format(filename, timestamp, last_successful_sync))
    last_success_timestamp = calendar.timegm(last_successful_sync.utctimetuple()) if last_successful_sync else None
    filename_allowed = filename.endswith('.csv') or filename.endswith('.csv.gz')
    file_uploaded_after_last_success = last_success_timestamp is None or timestamp > last_success_timestamp
    if not filename_allowed:
        current_app.logger.info(f'Skipping download of file #{filename}: File type not allowed.')
    elif not file_uploaded_after_last_success:
        current_app.logger.info(
            f'Skipping download of file #{filename}: Already processed successfully.'
        )
    return filename_allowed and file_uploaded_after_last_success


def get_files_in_sftp_url(
        host,
        user,
        password,
        path=".",
        port=22,
        last_successful_sync=None,
        check_subdir=False):
    current_app.logger.info('Getting files from {}, path: {}'.format(host, path))
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    port = port if port is not None else 22
    cinfo = {'host': host, 'port': port, 'username': user,
             'password': password, 'cnopts': cnopts}
    with pysftp.Connection(**cinfo) as sftp:
        sftp.timeout = 300.0  # Needs to be float. 300s is 50% of 600s set for task
        if path is not None:
            sftp.cwd(path)
        files = sftp.listdir_attr('.')
        csv_readers = []
        for attr in files:
            if check_subdir and sftp.isdir(attr.filename):
                new_path = os.path.join(path, attr.filename) if path else attr.filename
                csv_readers += get_files_in_sftp_url(
                    host, user, password, new_path, port, last_successful_sync, check_subdir)
            elif file_should_be_downloaded(attr.filename, attr.st_mtime, last_successful_sync):
                csv_readers.append(get_reader_from_sftp(sftp, attr.filename))
        sftp.close()
    return list(filter(None, csv_readers))


def get_reader_from_ftp(connection, filename):
    current_app.logger.info('Starting fo fetch file {}'.format(filename))
    bts = io.BytesIO()
    connection.retrbinary('RETR ' + filename, bts.write)
    current_app.logger.info('Got file {}'.format(filename))
    return get_reader_from_bytes(bts, filename)


def get_files_in_ftp_url(host, username=None, password=None, path='.', port=21, last_successful_sync=None):
    current_app.logger.info('Getting files from {}, path: {}'.format(host, path))
    port = port if port is not None else 21
    connection = FTP()
    connection.connect(host=host, port=port, timeout=300)
    connection.login(user=username, passwd=password)
    connection.cwd(path)
    files = connection.nlst()
    csv_readers = []
    for file in files:
        if file in [".", ".."]:
            continue
        modified_time = parser.parse(connection.voidcmd('MDTM {}'.format(file))[4:].strip())
        timestamp = datetime.timestamp(modified_time)
        if file_should_be_downloaded(file, timestamp, last_successful_sync):
            csv_readers.append(get_reader_from_ftp(connection, file))
    connection.quit()
    return list(filter(None, csv_readers))
