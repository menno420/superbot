"""Focused unit tests for ``youtube_fetch_service``.

Closes the Media/YouTube readiness "Fetch focused tests" Not-Done row: the
fetcher's URL parsing, the metadata-fetch error taxonomy, the content-free
provider-outcome diagnostics it records, and the transcript degrade-to-empty
contract.  All external I/O (aiohttp, the transcript API) is mocked — no real
network calls.
"""

from __future__ import annotations

import asyncio

import pytest

from services import youtube_diagnostics, youtube_fetch_service


# ---------------------------------------------------------------------------
# parse_video_id — pure, deterministic
# ---------------------------------------------------------------------------

_ID = "dQw4w9WgXcQ"  # canonical 11-char id


@pytest.mark.parametrize(
    "raw",
    [
        f"https://www.youtube.com/watch?v={_ID}",
        f"http://youtube.com/watch?v={_ID}",
        f"youtube.com/watch?v={_ID}",
        f"https://www.youtube.com/shorts/{_ID}",
        f"https://youtu.be/{_ID}",
        f"youtu.be/{_ID}",
        _ID,  # bare id
        f"  {_ID}  ",  # bare id with surrounding whitespace
        f"check this out https://youtu.be/{_ID}&feature=share",  # embedded in text
        f"https://www.youtube.com/watch?v={_ID}&t=30s",  # trailing query params
    ],
)
def test_parse_video_id_extracts_the_canonical_id(raw):
    assert youtube_fetch_service.parse_video_id(raw) == _ID


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "https://example.com/watch?v=dQw4w9WgXcQ",  # wrong host
        "https://vimeo.com/123456",
        "not a url at all",
        "shortid",  # < 11 chars, not a URL
        "waytoolongtobeavideoid12345",  # bare token wrong length
    ],
)
def test_parse_video_id_returns_none_for_non_matches(raw):
    assert youtube_fetch_service.parse_video_id(raw) is None


# ---------------------------------------------------------------------------
# fetch_video_metadata — aiohttp mocks + diagnostics outcome taxonomy
# ---------------------------------------------------------------------------


class _FakeResp:
    """Async-context-manager response stub matching aiohttp's surface."""

    def __init__(self, status: int, *, json_data=None, text_data: str = "") -> None:
        self.status = status
        self._json = json_data if json_data is not None else {}
        self._text = text_data

    async def __aenter__(self) -> "_FakeResp":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def json(self):
        return self._json

    async def text(self) -> str:
        return self._text


class _FakeSession:
    """``aiohttp.ClientSession()`` stub: async CM yielding a ``.get`` CM."""

    def __init__(self, *, resp: _FakeResp | None = None, raise_on_get=None) -> None:
        self._resp = resp
        self._raise_on_get = raise_on_get

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    def get(self, *args, **kwargs):
        if self._raise_on_get is not None:
            raise self._raise_on_get
        return self._resp


@pytest.fixture
def reset_diagnostics():
    youtube_diagnostics._reset_for_tests()
    yield
    youtube_diagnostics._reset_for_tests()


def _patch_session(monkeypatch, session: _FakeSession) -> None:
    monkeypatch.setattr(
        youtube_fetch_service.aiohttp,
        "ClientSession",
        lambda *a, **k: session,
    )


def _outcomes() -> dict[str, int]:
    return youtube_diagnostics.provider_outcome_counters()


async def test_missing_api_key_raises_and_records_key_missing(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", None)
    with pytest.raises(youtube_fetch_service.YouTubeFetchError) as exc:
        await youtube_fetch_service.fetch_video_metadata(_ID)
    assert exc.value.reason == "youtube_api_key_missing"
    assert exc.value.retryable is False
    assert _outcomes()["key_missing"] == 1


async def test_success_returns_item_and_records_success(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", "fake-key")
    item = {"snippet": {"title": "x"}}
    _patch_session(
        monkeypatch,
        _FakeSession(resp=_FakeResp(200, json_data={"items": [item]})),
    )
    result = await youtube_fetch_service.fetch_video_metadata(_ID)
    assert result == item
    assert _outcomes()["success"] == 1


async def test_quota_exceeded_403_records_quota_limited(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", "fake-key")
    _patch_session(
        monkeypatch,
        _FakeSession(resp=_FakeResp(403, text_data='{"error": "quotaExceeded"}')),
    )
    with pytest.raises(youtube_fetch_service.YouTubeFetchError) as exc:
        await youtube_fetch_service.fetch_video_metadata(_ID)
    assert exc.value.reason == "quota_limited"
    assert _outcomes()["quota_limited"] == 1


async def test_other_403_records_fetch_error(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", "fake-key")
    _patch_session(
        monkeypatch,
        _FakeSession(resp=_FakeResp(403, text_data='{"error": "forbidden"}')),
    )
    with pytest.raises(youtube_fetch_service.YouTubeFetchError) as exc:
        await youtube_fetch_service.fetch_video_metadata(_ID)
    assert exc.value.reason == "fetch_error"
    assert _outcomes()["fetch_error"] == 1


async def test_5xx_is_retryable_fetch_error(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", "fake-key")
    _patch_session(monkeypatch, _FakeSession(resp=_FakeResp(503)))
    with pytest.raises(youtube_fetch_service.YouTubeFetchError) as exc:
        await youtube_fetch_service.fetch_video_metadata(_ID)
    assert exc.value.reason == "fetch_error"
    assert exc.value.retryable is True
    assert _outcomes()["fetch_error"] == 1


async def test_4xx_non_403_is_non_retryable_fetch_error(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", "fake-key")
    _patch_session(monkeypatch, _FakeSession(resp=_FakeResp(404)))
    with pytest.raises(youtube_fetch_service.YouTubeFetchError) as exc:
        await youtube_fetch_service.fetch_video_metadata(_ID)
    assert exc.value.reason == "fetch_error"
    assert exc.value.retryable is False


async def test_empty_items_is_private_or_deleted(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", "fake-key")
    _patch_session(
        monkeypatch,
        _FakeSession(resp=_FakeResp(200, json_data={"items": []})),
    )
    with pytest.raises(youtube_fetch_service.YouTubeFetchError) as exc:
        await youtube_fetch_service.fetch_video_metadata(_ID)
    assert exc.value.reason == "video_private_or_deleted"
    assert _outcomes()["private_or_deleted"] == 1


async def test_timeout_records_timeout_and_reraises(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", "fake-key")
    _patch_session(
        monkeypatch,
        _FakeSession(raise_on_get=asyncio.TimeoutError()),
    )
    with pytest.raises(asyncio.TimeoutError):
        await youtube_fetch_service.fetch_video_metadata(_ID)
    assert _outcomes()["timeout"] == 1


async def test_unexpected_error_records_fetch_error_and_reraises(monkeypatch, reset_diagnostics):
    monkeypatch.setattr(youtube_fetch_service, "_API_KEY", "fake-key")
    _patch_session(
        monkeypatch,
        _FakeSession(raise_on_get=RuntimeError("boom")),
    )
    with pytest.raises(RuntimeError):
        await youtube_fetch_service.fetch_video_metadata(_ID)
    assert _outcomes()["fetch_error"] == 1


# ---------------------------------------------------------------------------
# fetch_transcript — degrade-to-empty contract
# ---------------------------------------------------------------------------


class _FakeTranscriptApi:
    def __init__(self, *, segments=None, raise_exc=None) -> None:
        self._segments = segments or []
        self._raise = raise_exc

    def fetch(self, video_id):  # noqa: ARG002 — signature parity
        if self._raise is not None:
            raise self._raise
        return self

    def to_raw_data(self):
        return self._segments


def _inject_transcript_api(monkeypatch, api) -> None:
    import sys
    import types

    module = types.ModuleType("youtube_transcript_api")
    module.YouTubeTranscriptApi = lambda: api
    monkeypatch.setitem(sys.modules, "youtube_transcript_api", module)


async def test_fetch_transcript_returns_segments(monkeypatch):
    segs = [{"text": "hello", "start": 0.0}, {"text": "world", "start": 1.0}]
    _inject_transcript_api(monkeypatch, _FakeTranscriptApi(segments=segs))
    result = await youtube_fetch_service.fetch_transcript(_ID)
    assert result == segs


async def test_fetch_transcript_returns_empty_on_error(monkeypatch):
    _inject_transcript_api(
        monkeypatch,
        _FakeTranscriptApi(raise_exc=RuntimeError("no transcript")),
    )
    result = await youtube_fetch_service.fetch_transcript(_ID)
    assert result == []
