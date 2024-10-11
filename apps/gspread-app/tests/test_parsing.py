import pytest
from app import create_app
from src import feed_parser
from src.exceptions import MalformedCsvException
from tests.fixtures import example_gspread

# Setup for preventing current_app.logger from causing errors
ctx = create_app().app_context()
ctx.push()


@pytest.fixture
def example_input_from_gspread():
    return example_gspread.example_input(True)


@pytest.fixture
def malformed_input_from_gspread():
    return example_gspread.example_input(False)


def test_that_the_output_generates_correctly(example_input_from_gspread):
    output = feed_parser.write_to_csv(example_input_from_gspread)
    length = len(output.splitlines())
    assert length == 3


def test_that_throws_csv_malformed_exception_if_csv_not_as_expected(
    malformed_input_from_gspread,
):
    with pytest.raises(
        MalformedCsvException,
        match="('Could not create a csv file. Column count does not match', {'expected': 30, 'got_insted': 31})",
    ):
        feed_parser.write_to_csv(malformed_input_from_gspread)
