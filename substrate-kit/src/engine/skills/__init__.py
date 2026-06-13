"""Skills — the invoke-a-capability layer (plan section 3c).

A skill is an invokable ``SKILL.md`` procedure (the counterpart to a stance's
ambient posture). The kit ships generalized skill *sources* here and emits native
``.claude/skills/<name>/SKILL.md`` files (metadata-first frontmatter + body) so
they load progressively and port across agent CLIs.
"""
