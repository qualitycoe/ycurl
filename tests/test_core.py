import pytest
from ycurl.core import perform_request


def test_perform_request_basic(monkeypatch):
    class MockResponse:
        status_code = 200
        headers = {"Content-Type": "application/json"}
        text = '{"message": "success"}'

    def mock_request(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("requests.request", mock_request)

    config = {"base_url": "http://example.com", "method": "GET"}

    resp = perform_request(config)
    assert resp.status_code == 200
