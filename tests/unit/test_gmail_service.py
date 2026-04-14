"""Unit tests for Gmail service helper functions."""

from __future__ import annotations

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response

from app.services.gmail import fetch_history_since


class _FakeRequest:
    def __init__(self, response: dict | None = None, error: Exception | None = None):
        self._response = response
        self._error = error

    def execute(self):
        if self._error is not None:
            raise self._error
        return self._response


class _FakeHistoryResource:
    def __init__(self, responses: list[dict], error_on_call: int | None = None):
        self._responses = responses
        self._call_count = 0
        self._error_on_call = error_on_call

    def list(self, **kwargs):  # noqa: ARG002
        self._call_count += 1
        if self._error_on_call is not None and self._call_count == self._error_on_call:
            response = Response({"status": "500"})
            return _FakeRequest(
                error=HttpError(response, b'{"error":{"message":"history failed"}}')
            )

        index = self._call_count - 1
        return _FakeRequest(response=self._responses[index])


class _FakeUsersResource:
    def __init__(self, history_resource: _FakeHistoryResource):
        self._history_resource = history_resource

    def history(self):
        return self._history_resource


class _FakeService:
    def __init__(self, history_resource: _FakeHistoryResource):
        self._users_resource = _FakeUsersResource(history_resource)

    def users(self):
        return self._users_resource


class TestFetchHistorySince:
    def test_returns_unique_thread_ids_and_latest_history_id(self):
        history_resource = _FakeHistoryResource(
            responses=[
                {
                    "historyId": "101",
                    "history": [
                        {
                            "messagesAdded": [
                                {"message": {"threadId": "thread-1"}},
                                {"message": {"threadId": "thread-1"}},
                            ]
                        }
                    ],
                    "nextPageToken": "next",
                },
                {
                    "historyId": "105",
                    "history": [
                        {
                            "messagesAdded": [
                                {"message": {"threadId": "thread-2"}},
                            ]
                        }
                    ],
                },
            ]
        )
        service = _FakeService(history_resource)

        result = fetch_history_since(service, start_history_id="100")

        assert result.thread_ids == ["thread-1", "thread-2"]
        assert result.latest_history_id == "105"

    def test_raises_when_history_api_fails(self):
        history_resource = _FakeHistoryResource(
            responses=[{"historyId": "101", "history": []}],
            error_on_call=1,
        )
        service = _FakeService(history_resource)

        with pytest.raises(HttpError):
            fetch_history_since(service, start_history_id="100")
