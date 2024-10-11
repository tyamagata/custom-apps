import requests
from app.helpers import bytesio_md5, get_csv_reader, detect_encoding


class HTTPDownloadException(Exception):
    pass


def get_file_from_url(url):
    response = requests.get(url)
    if response.ok:
        content = response.content
        encoding = detect_encoding(content)
        md5 = bytesio_md5(content)
        csv_reader = get_csv_reader(content.decode(encoding).splitlines())
        return (csv_reader, md5, url)
    else:
        raise HTTPDownloadException(
            "Error in downloading file from '{}': status {}, body: {}".format(
                url, response.status_code, response.content))
