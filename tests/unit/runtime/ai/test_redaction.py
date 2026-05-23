"""Tests for ``core.runtime.ai.redaction`` — every regex exercised with
positive and negative samples, plus idempotency and nested-payload
coverage (LP-1).
"""

from __future__ import annotations

import pytest

from core.runtime.ai.redaction import redact_payload, redact_text

# Built at runtime so the .py source never contains a 3-part base64-shaped
# literal — GitHub's secret scanner would flag any such string as a possible
# Discord bot token even when every part is a single repeated character.
_DISCORD_TOKEN_FIXTURE = ".".join(("a" * 24, "b" * 8, "c" * 21))

# (input, expected_label, marker_must_appear_in_output)
_POSITIVE_CASES = [
    # discord_token_like — three base64-ish parts (23+ . 6+ . 20+)
    (
        _DISCORD_TOKEN_FIXTURE,
        "discord_token_like",
        "[discord_token_like:redacted]",
    ),
    # api_key_like — sk_/pk_/rk_/xoxb_/ghp_ + 12+ chars
    ("sk_live_abc123def456ghi", "api_key_like", "[api_key_like:redacted]"),
    ("ghp_1234567890abcdefghij", "api_key_like", "[api_key_like:redacted]"),
    ("xoxb_long_enough_token_value", "api_key_like", "[api_key_like:redacted]"),
    # database_url
    ("postgres://user:pass@host:5432/db", "database_url", "[database_url:redacted]"),
    ("postgresql://u:p@example.com:5432/x", "database_url", "[database_url:redacted]"),
    # bearer_token (case-insensitive)
    ("Authorization: Bearer abc.def-123", "bearer_token", "[bearer_token:redacted]"),
    ("bearer abc.def-123", "bearer_token", "[bearer_token:redacted]"),
    # email
    ("Contact alice@example.com please", "email", "[email:redacted]"),
    # url_secret_query — token/key/secret/password/signature
    (
        "https://api.example.com/x?token=foo&other=baz",
        "url_secret_query",
        "?token=[redacted]",
    ),
    (
        "https://api.example.com/x?other=baz&password=hunter2",
        "url_secret_query",
        "&password=[redacted]",
    ),
]


@pytest.mark.parametrize("text,label,marker", _POSITIVE_CASES)
def test_redact_text_matches_known_secret_shapes(
    text: str, label: str, marker: str
) -> None:
    result = redact_text(text)
    assert result.replacements.get(label) == 1, (
        f"expected one match for {label!r} in {text!r}; got {result.replacements}"
    )
    assert marker in result.value, (
        f"marker {marker!r} missing from redacted output {result.value!r}"
    )


_NEGATIVE_CASES = [
    "a.b.c",  # discord_token_like — too short
    "sk_short",  # api_key_like — under 12 chars after the prefix
    "https://example.com/page",  # database_url — wrong scheme
    "Carrier abc-def-1234",  # bearer_token — wrong keyword
    "@example.com",  # email — missing local part
    "?other=foo",  # url_secret_query — non-secret key name
    "Hello world.",
    "1234567890",
    "",
]


@pytest.mark.parametrize("text", _NEGATIVE_CASES)
def test_redact_text_leaves_non_secret_strings_alone(text: str) -> None:
    result = redact_text(text)
    assert result.value == text
    assert not result.replacements


def test_redact_text_redacts_multiple_secrets_in_one_string() -> None:
    text = "key sk_live_abcdef123456 and postgres://x:y@h/d"
    result = redact_text(text)
    assert result.replacements.get("api_key_like") == 1
    assert result.replacements.get("database_url") == 1
    assert "[api_key_like:redacted]" in result.value
    assert "[database_url:redacted]" in result.value


def test_redact_text_is_idempotent_on_already_redacted_output() -> None:
    once = redact_text("sk_live_abcdef123456").value
    twice = redact_text(once)
    assert twice.value == once
    assert not twice.replacements


def test_redact_payload_walks_dicts_lists_tuples() -> None:
    payload = {
        "outer": "no secrets",
        "nested": ["sk_live_abcdef123456", {"deep": "postgres://u:p@h/d"}],
        "tup": ("Bearer abc-def-1234",),
    }
    result = redact_payload(payload)
    assert result.replacements.get("api_key_like") == 1
    assert result.replacements.get("database_url") == 1
    assert result.replacements.get("bearer_token") == 1
    assert result.value["outer"] == "no secrets"
    assert "[api_key_like:redacted]" in result.value["nested"][0]
    assert "[database_url:redacted]" in result.value["nested"][1]["deep"]
    assert "[bearer_token:redacted]" in result.value["tup"][0]


def test_redact_payload_preserves_non_string_leaves() -> None:
    payload = {"count": 42, "flag": True, "none": None, "nested": [1, 2, 3]}
    result = redact_payload(payload)
    assert result.value == payload
    assert not result.replacements
