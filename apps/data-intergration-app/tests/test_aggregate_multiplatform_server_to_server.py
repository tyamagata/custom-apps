import pytest
import responses
from app.aggregate_multiplatform_server_to_server import AggregateMultiplatformServerToServerSender
from app.helpers import get_csv_reader
from app.parsers.example_aggregate_multiplatform_server_to_server import ExampleAggregateS2SParser
import os


event_with_all_fields = {
    'platform': 'facebook',
    'ad_unit_id': '12345',
    'event_name': 'purchase',
    'ad_interaction_time': '12345',
    'event_time': '9876',
    'install_time': '12345',
    'conversions': 'conversions',
    'value': 'somevalue',
    'value_currency': 'eur'
    }


@pytest.fixture(autouse=True, scope="module")
def set_environment():
    os.environ['supersecret'] = 'foo'
    yield
    del os.environ['supersecret']


@responses.activate
def test_failures():
    responses.add(
        responses.POST,
        '[FILL ME IN S2S ENDPOINT]',
        status=500,
        json={},
        match_querystring=False)

    with open('tests/fixtures/aggregate_multiplatform_s2s_example.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = ExampleAggregateS2SParser(reader)
    s2s_data = parser.to_aggregate_multiplatform_s2s_events()
    os.environ['supersecret'] = 'foo'
    s2s_sender = AggregateMultiplatformServerToServerSender(s2s_data, "supersecret")

    assert len(responses.calls) == 0
    result = s2s_sender.send()
    assert len(responses.calls) == 4  # no retries,
    assert len(s2s_data) == 4  # only 4 separate requests,
    assert result['failures'] == 4  # each only
    assert result['successes'] == 0


@responses.activate
def test_successfull_http_calls():
    s2s_event_urls = ('[FILL ME IN S2S ENDPOINT]')

    def request_callback(request):
        assert request.url in s2s_event_urls
        return (200, {}, 'GIF')

    responses.add_callback(
        responses.POST, '[FILL ME IN S2S ENDPOINT]',
        callback=request_callback,
        content_type='application/json',
    )

    with open('tests/fixtures/aggregate_multiplatform_s2s_example.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = ExampleAggregateS2SParser(reader)
    s2s_data = parser.to_aggregate_multiplatform_s2s_events()
    os.environ['supersecret'] = 'foo'
    s2s_sender = AggregateMultiplatformServerToServerSender(s2s_data, "supersecret")
    result = s2s_sender.send()

    assert len(responses.calls) == 4
    assert result['successes'] == 4


def test_to_multiplatform_s2s_event_exception_handling():
    s2s_sender = AggregateMultiplatformServerToServerSender([], 'supersecret')

    with pytest.raises(Exception) as e:
        s2s_sender.to_aggregate_multiplatform_s2s_event({})

    assert 'Required field: platform' in str(e.value)


def test_to_multiplatform_s2s_event_required_fields():
    s2s_sender = AggregateMultiplatformServerToServerSender([], 'supersecret')
    required_fields = {
        'platform': 'facebook',
        'ad_unit_id': '12345',
        'event_name': 'purchase',
        'ad_interaction_time': '12345'
        }
    result = s2s_sender.to_aggregate_multiplatform_s2s_event(required_fields)
    assert result == required_fields


def test_to_multiplatform_s2s_event_optional_fields():
    s2s_sender = AggregateMultiplatformServerToServerSender([], 'supersecret')
    result = s2s_sender.to_aggregate_multiplatform_s2s_event(event_with_all_fields)
    assert result == event_with_all_fields


def test_to_multiplatform_s2s_event_invalid_fields():
    s2s_sender = AggregateMultiplatformServerToServerSender([], 'supersecret')
    event_with_invalid_fields = {**event_with_all_fields, 'invalid_field': 'invalid'}
    result = s2s_sender.to_aggregate_multiplatform_s2s_event(event_with_invalid_fields)
    assert result == event_with_all_fields
