"""Generic, config-driven hygiene checkers lifted from the host project.

These are stdlib-only ports of the proven ``check_docs`` / ``check_session_log``
scripts, with every host-specific value (doc root, badge taxonomy, read-path
docs, sessions dir, required markers) read from ``substrate.config.json`` instead
of hardcoded. The host project's ratchets and freshness rules are intentionally
dropped — they are superbot-shaped policy, not portable mechanism.
"""
