import responses
from app.server_to_server import ServerToServerSender
from app.helpers import get_csv_reader
from app.parsers.example_server_to_server import ExampleServerToServerParser


@responses.activate
def test_failures():
    responses.add(
        responses.GET,
        '[FILL ME IN S2S ENDPOINT]',
        status=500,
        match_querystring=False)

    with open('tests/fixtures/s2s_example.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = ExampleServerToServerParser(reader)
    s2s_data = parser.to_s2s_events()
    s2s_sender = ServerToServerSender(s2s_data)

    assert len(responses.calls) == 0
    result = s2s_sender.send()
    assert len(responses.calls) == 4
    assert len(s2s_data) == 4
    assert result['failures'] == 4
    assert result['successes'] == 0


@responses.activate
def test_successfull_http_calls():
    s2s_event_urls = (
        '[FILL ME IN S2S ENDPOINT]') # noqa

    def request_callback(request):
        assert request.url in s2s_event_urls
        return (200, {}, 'GIF')

    responses.add_callback(
        responses.GET, '[FILL ME IN S2S ENDPOINT]',
        callback=request_callback,
        content_type='application/json',
    )

    with open('tests/fixtures/s2s_example.csv') as infile:
        csv_data = infile.read().splitlines()

    reader = get_csv_reader(csv_data)
    parser = ExampleServerToServerParser(reader)
    s2s_data = parser.to_s2s_events()

    s2s_sender = ServerToServerSender(s2s_data)
    result = s2s_sender.send()

    assert len(responses.calls) == 4
    assert result['successes'] == 4
