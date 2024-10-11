import csv
import io

from flask import current_app
from src.exceptions import MalformedCsvException


def write_to_csv(output):
    if current_app:
        current_app.logger.info("Writing the final feed")
    si = io.StringIO()
    feed_writer = csv.writer(
        si, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
    )
    count_headers = len(output[0])
    for row in output:
        check_valid_csv(count_headers, row)
        feed_writer.writerow(row)
    return si.getvalue()


def check_valid_csv(number_of_headers, row):
    if number_of_headers != len(row):
        raise MalformedCsvException(
            "Could not create a csv file. Column count does not match",
            {"expected": number_of_headers, "got_insted": len(row)},
        )
