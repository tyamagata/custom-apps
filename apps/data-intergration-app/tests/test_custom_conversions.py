import pytest
import responses
import os
from app.custom_conversions import CustomConversionSender, CustomConversionSenderException
from app.helpers import get_csv_reader
from app.parsers.visualiq import VisualIqParser
from requests.exceptions import HTTPError
from decimal import Decimal


@pytest.fixture(autouse=True)
def clean_environment():
    if os.environ.get('supersecret'):
        del os.environ['supersecret']
    yield


def test_generating_payload():
    with open('tests/fixtures/visualiq.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = VisualIqParser(reader)
    custom_conversion_data = parser.to_custom_conversions()

    custom_conversion_sender = CustomConversionSender(
        custom_conversion_data, 'supersecret')
    payloads = custom_conversion_sender._generate_api_payloads()
    assert len(payloads) == 1

    assert payloads[0]['ignore_invalid_ad_ids'] is True
    assert payloads[0]['data'][0]['date'] == '2019-01-02'
    assert payloads[0]['data'][0]['ad_id'] == '6112314979164'
    assert payloads[0]['data'][0]['type'] == 'Visual IQ PAX'
    assert payloads[0]['data'][0]['value'] == Decimal('0.513848')
    assert payloads[0]['data'][0]['actions'] == Decimal('0.000688')


def test_raises_error_when_api_token_is_missing():
    with open('tests/fixtures/visualiq.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = VisualIqParser(reader)
    custom_conversion_data = parser.to_custom_conversions()

    custom_conversion_sender = CustomConversionSender(
        custom_conversion_data, 'supersecret')
    with pytest.raises(CustomConversionSenderException) as e:
        custom_conversion_sender.send()
    assert 'Missing API token from ENV' in str(e.value)


@responses.activate
def test_raises_an_error_when_http_call_not_successful():
    responses.add(
        responses.POST,
        '[FILL ME IN S2S ENDPOINT]',
        status=500)

    with open('tests/fixtures/visualiq.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = VisualIqParser(reader)
    custom_conversion_data = parser.to_custom_conversions()
    os.environ['supersecret'] = 'foo'
    custom_conversion_sender = CustomConversionSender(
        custom_conversion_data, 'supersecret')
    with pytest.raises(HTTPError):
        custom_conversion_sender.send()


@responses.activate
def test_with_empty_data_skips_api_request():
    # Custom conversion import API rejects empty data
    responses.add(
        responses.POST,
        '[FILL ME IN S2S ENDPOINT]',
        status=400
    )

    os.environ['supersecret'] = 'foo'
    custom_conversion_sender = CustomConversionSender(
        [], 'supersecret')
    result = custom_conversion_sender.send()
    assert result['successes'] == 0
    assert result['failures'] == 0
    assert len(responses.calls) == 0


@responses.activate
def test_successfull_http_call():
    responses.add(
        responses.POST,
        '[FILL ME IN S2S ENDPOINT]',
        status=200,
        json={
            'count': 3})

    with open('tests/fixtures/visualiq.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = VisualIqParser(reader)
    custom_conversion_data = parser.to_custom_conversions()
    os.environ['supersecret'] = 'foo'
    custom_conversion_sender = CustomConversionSender(
        custom_conversion_data, 'supersecret')
    result = custom_conversion_sender.send()
    assert result['successes'] == 3


@responses.activate
def test_successful_sending_wilh_multiple_batches():
    responses.add(
        responses.POST,
        '[FILL ME IN S2S ENDPOINT]',
        status=200,
        json={
            'count': 10000})

    with open('tests/fixtures/visualiq.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = VisualIqParser(reader)
    custom_conversion_data = parser.to_custom_conversions()
    multiplied_data = []
    for i in range(10000):
        multiplied_data += custom_conversion_data
    os.environ['supersecret'] = 'foo'
    custom_conversion_sender = CustomConversionSender(
        multiplied_data, 'supersecret')
    result = custom_conversion_sender.send()
    assert result['successes'] == 30000


def test_chunks():
    data = range(10)
    chunks = list(CustomConversionSender.chunks(data, 5))
    assert len(chunks) == 5
    assert len(chunks[0]) == 2

    data = range(10)
    chunks = list(CustomConversionSender.chunks(data, 3))
    assert len(chunks) == 3
    num_of_items_in_total = 0
    for chunk in chunks:
        num_of_items_in_total += len(list(chunk))
    assert num_of_items_in_total == 10


def test_get_chunk_size():
    custom_conversions_sender = CustomConversionSender(range(10000), 'foo')
    chunk_size = custom_conversions_sender.get_chunk_size()
    assert chunk_size == 1

    custom_conversions_sender = CustomConversionSender(range(20000), 'foo')
    chunk_size = custom_conversions_sender.get_chunk_size()
    assert chunk_size == 2

    custom_conversions_sender = CustomConversionSender(range(20010), 'foo')
    chunk_size = custom_conversions_sender.get_chunk_size()
    assert chunk_size == 3
