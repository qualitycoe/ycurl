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


def test_body_from_file(tmp_path, monkeypatch):
    # Create test JSON file
    payload = tmp_path / "test_payload.json"
    payload.write_text('{"test": "value"}')

    class MockResponse:
        status_code = 200
        headers = {}
        text = '{"message": "OK"}'

    monkeypatch.setattr("requests.request", lambda *a, **kw: MockResponse())

    config = {
        "base_url": "http://example.com",
        "method": "POST",
        "body_from_file": str(payload),
    }

    resp = perform_request(config)
    assert resp.status_code == 200
