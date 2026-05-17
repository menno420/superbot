"""S5.1 — IDENTITY_CONTRACT_STRICT is default-on with STRICT_DISABLED escape.

Pre-S5.1 the validator ran in Advisory mode unless explicitly
opted-in via IDENTITY_CONTRACT_STRICT=true.  S5.1 flipped the
default so every deploy refuses to start on fatal-tier drift unless
the operator explicitly opts out via STRICT_DISABLED=1 (canonical
escape hatch) or IDENTITY_CONTRACT_STRICT=false (legacy opt-out).

The truth table:

  STRICT_DISABLED | IDENTITY_CONTRACT_STRICT | _identity_contract_strict()
  ----------------|--------------------------|----------------------------
  unset           | unset                    | True   (new default)
  unset           | true                     | True   (redundant, fine)
  unset           | false                    | False  (legacy opt-out)
  1               | <anything>               | False  (canonical escape)
"""

from __future__ import annotations

import pytest


@pytest.fixture
def _clean_env(monkeypatch):
    """Unset both env vars so each test starts from a known state."""
    monkeypatch.delenv("STRICT_DISABLED", raising=False)
    monkeypatch.delenv("IDENTITY_CONTRACT_STRICT", raising=False)
    yield monkeypatch


def _strict() -> bool:
    """Re-import + call to bypass any import-time caching."""
    from bot1 import _identity_contract_strict

    return _identity_contract_strict()


# ---------------------------------------------------------------------------
# Default-on (the actual flip)
# ---------------------------------------------------------------------------


def test_strict_is_on_when_both_env_vars_unset(_clean_env):
    """The S5.1 promotion: STRICT runs by default."""
    assert _strict() is True


# ---------------------------------------------------------------------------
# Canonical opt-out — STRICT_DISABLED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE", "Yes"])
def test_strict_off_when_STRICT_DISABLED_is_truthy(_clean_env, value):
    _clean_env.setenv("STRICT_DISABLED", value)
    assert _strict() is False


@pytest.mark.parametrize("value", ["0", "false", "", "no", "off"])
def test_strict_on_when_STRICT_DISABLED_is_falsy_or_empty(_clean_env, value):
    _clean_env.setenv("STRICT_DISABLED", value)
    assert _strict() is True


# ---------------------------------------------------------------------------
# Legacy opt-out — IDENTITY_CONTRACT_STRICT=false
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "FALSE", "No"])
def test_strict_off_when_legacy_var_explicitly_disables(_clean_env, value):
    _clean_env.setenv("IDENTITY_CONTRACT_STRICT", value)
    assert _strict() is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on"])
def test_strict_on_when_legacy_var_is_truthy(_clean_env, value):
    """Truthy legacy var is redundant under the new default but still
    produces STRICT — no behaviour change for operators who set it."""
    _clean_env.setenv("IDENTITY_CONTRACT_STRICT", value)
    assert _strict() is True


# ---------------------------------------------------------------------------
# Precedence — STRICT_DISABLED wins
# ---------------------------------------------------------------------------


def test_STRICT_DISABLED_overrides_legacy_truthy_var(_clean_env):
    """Both set → STRICT_DISABLED is the canonical escape and wins."""
    _clean_env.setenv("STRICT_DISABLED", "1")
    _clean_env.setenv("IDENTITY_CONTRACT_STRICT", "true")
    assert _strict() is False


def test_legacy_false_still_disables_even_with_STRICT_DISABLED_unset(_clean_env):
    """Belt-and-braces: legacy opt-out works even without the new var set."""
    _clean_env.setenv("IDENTITY_CONTRACT_STRICT", "false")
    assert _strict() is False
