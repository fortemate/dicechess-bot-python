"""Hermetic tests for ``BotClient`` retry handling — urllib is stubbed, nothing touches the network."""

import io
import json
import unittest
import urllib.error
from unittest import mock

from dicechess import ApiError, BotClient


def _http_error(status: int, headers: dict | None = None) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x/y", status, "err", headers or {}, io.BytesIO(b"detail"))


class _Response:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._data


class RequestRetryTests(unittest.TestCase):
    def _call(self, outcomes, **client_kwargs):
        client = BotClient(base_url="http://x", token="t", **client_kwargs)
        with (
            mock.patch("urllib.request.urlopen", side_effect=outcomes) as urlopen,
            mock.patch("time.sleep") as sleep,
        ):
            try:
                result = client._request("GET", "/p")
            except Exception as e:  # noqa: BLE001 - the tests assert on the exception type
                result = e
        return result, urlopen.call_count, [c.args[0] for c in sleep.call_args_list]

    def test_success_needs_one_call(self):
        result, calls, sleeps = self._call([_Response({"ok": True})])
        self.assertEqual(result, {"ok": True})
        self.assertEqual((calls, sleeps), (1, []))

    def test_server_error_backs_off_exponentially_then_succeeds(self):
        result, calls, sleeps = self._call([_http_error(503), _http_error(500), _Response({"ok": 1})])
        self.assertEqual(result, {"ok": 1})
        self.assertEqual((calls, sleeps), (3, [1.0, 2.0]))

    def test_rate_limit_honours_retry_after(self):
        result, _calls, sleeps = self._call([_http_error(429, {"Retry-After": "7"}), _Response({"ok": 1})])
        self.assertEqual(result, {"ok": 1})
        self.assertEqual(sleeps, [7.0])

    def test_unauthorized_refreshes_token_and_retries_without_waiting(self):
        refreshed = []
        result, calls, sleeps = self._call(
            [_http_error(401), _Response({"ok": 1})], on_unauthorized=lambda c: refreshed.append(c)
        )
        self.assertEqual(result, {"ok": 1})
        self.assertEqual((len(refreshed), calls, sleeps), (1, 2, [0.0]))

    def test_unauthorized_without_hook_is_final(self):
        result, calls, _ = self._call([_http_error(401)])
        self.assertIsInstance(result, ApiError)
        self.assertEqual((result.status, calls), (401, 1))

    def test_client_error_is_not_retried(self):
        result, calls, _ = self._call([_http_error(404)])
        self.assertIsInstance(result, ApiError)
        self.assertEqual((result.status, result.body, calls), (404, "detail", 1))

    def test_retries_are_bounded(self):
        result, calls, _ = self._call([_http_error(503)] * 10, max_retries=2)
        self.assertIsInstance(result, ApiError)
        self.assertEqual(calls, 3)

    def test_network_error_is_retried_then_raised(self):
        err = urllib.error.URLError("down")
        result, calls, sleeps = self._call([err, err, err], max_retries=2)
        self.assertIsInstance(result, urllib.error.URLError)
        self.assertEqual((calls, sleeps), (3, [1.0, 2.0]))


if __name__ == "__main__":
    unittest.main()
