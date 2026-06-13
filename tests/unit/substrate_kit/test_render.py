"""Tests for the template render mechanism + template/bank coherence."""

import build_bootstrap
from engine.interview.question_bank import QUESTIONS
from engine.render import build_context, find_placeholders, load_templates, render


def test_find_placeholders():
    assert find_placeholders("${a} text ${b}") == {"a", "b"}
    assert find_placeholders("no placeholders here") == set()


def test_render_substitutes_filled_and_leaves_unfilled_visible():
    out = render("Hello ${name}, welcome to ${place}.", {"name": "Ada"})
    assert "Ada" in out
    assert "${place}" in out  # unfilled slot stays visible, not blank


def test_build_context_from_slot_values():
    state = {"slot_values": {"project_name": {"value": "Demo"}}}
    assert build_context(state) == {"project_name": "Demo"}


def test_load_templates_returns_core_set():
    templates = load_templates()
    assert "CLAUDE.md.tmpl" in templates
    assert "AGENT_ORIENTATION.md.tmpl" in templates
    assert "current-state.md.tmpl" in templates


def test_templates_only_reference_known_bank_slots():
    # Every placeholder must map to a bank slot, so a fully-filled interview
    # renders with zero leftovers (template/bank coherence guard).
    bank_slots = {q["slot"] for q in QUESTIONS}
    for name, text in load_templates().items():
        unknown = find_placeholders(text) - bank_slots
        assert not unknown, f"{name} references non-bank slots: {unknown}"


def test_full_fill_renders_without_leftovers():
    context = {q["slot"]: f"v-{q['slot']}" for q in QUESTIONS}
    for name, text in load_templates().items():
        assert find_placeholders(render(text, context)) == set(), name


def test_templates_embedded_in_bootstrap():
    assert "_TEMPLATES = {" in build_bootstrap.build()
