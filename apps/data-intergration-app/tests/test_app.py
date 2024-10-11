def test_health_endpoint(client):
    response = client.get('/health')
    assert b'OK' == response.data
