"""Personas — spawnable read-only specialists (plan section 3c).

A persona is a sub-agent the working agent can spawn for a focused, read-only
task (design review, independent critique, deep exploration). The kit ships
generalized persona sources here and emits native ``.claude/agents/<name>.md``
files (frontmatter + system-prompt body), each filled from the project's own
contract docs via ``${slot}`` substitution.
"""
