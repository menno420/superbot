"""Tests for YouTube URL routing in ai_task_router."""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import AITask  # noqa: E402
from services import ai_task_router  # noqa: E402


def test_two_youtube_urls_routes_to_compare():
    result = ai_task_router.classify(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ https://youtu.be/abcdefghijk"
    )
    assert result.task is AITask.VIDEO_COMPARE
    assert result.route == "video.compare"
    assert result.confidence == 0.90


def test_one_url_with_question_routes_to_qa():
    result = ai_task_router.classify(
        "what is this video about? https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert result.task is AITask.VIDEO_QA
    assert result.route == "video.qa"
    assert result.confidence == 0.80


def test_one_url_without_question_routes_to_describe():
    result = ai_task_router.classify("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert result.task is AITask.VIDEO_DESCRIBE
    assert result.route == "video.describe"
    assert result.confidence == 0.85


def test_shorts_url_routes_to_describe():
    result = ai_task_router.classify("https://www.youtube.com/shorts/dQw4w9WgXcQ")
    assert result.task is AITask.VIDEO_DESCRIBE


def test_youtu_be_url_routes_to_describe():
    result = ai_task_router.classify("https://youtu.be/dQw4w9WgXcQ")
    assert result.task is AITask.VIDEO_DESCRIBE


def test_no_url_no_video_route():
    result = ai_task_router.classify("what is the best tower?")
    assert result.task is not AITask.VIDEO_DESCRIBE
    assert result.task is not AITask.VIDEO_QA
    assert result.task is not AITask.VIDEO_COMPARE


def test_url_with_explain_keyword_routes_to_qa():
    result = ai_task_router.classify(
        "explain https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert result.task is AITask.VIDEO_QA


def test_two_urls_always_compare_regardless_of_question():
    result = ai_task_router.classify(
        "what is the difference? https://youtu.be/aaaaaaaaaaa https://youtu.be/bbbbbbbbbbb"
    )
    assert result.task is AITask.VIDEO_COMPARE


def test_btd6_text_still_routes_btd6_even_with_url():
    result = ai_task_router.classify(
        "what's the bloons strategy for https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert result.task is AITask.BTD6_ANSWER
