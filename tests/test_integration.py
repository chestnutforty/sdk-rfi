"""Integration tests against the live RFI API.

These tests make REAL API calls and verify responses.

Run with:
    RFI_EMAIL=... RFI_PASSWORD=... uv run pytest tests/test_integration.py -v
"""

from __future__ import annotations

import os

import pytest

from sdk_rfi import Client, AsyncClient

# Skip all tests if credentials not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("RFI_EMAIL") or not os.environ.get("RFI_PASSWORD"),
    reason="RFI_EMAIL and RFI_PASSWORD not set",
)


class TestAuthentication:
    """Test OAuth2 authentication."""

    def test_auth_with_env_vars(self) -> None:
        """Client authenticates using env vars."""
        with Client() as client:
            # Just creating the client should work
            # Token is fetched lazily on first request
            result = client.questions.list()
            assert result is not None

    def test_auth_with_explicit_credentials(self) -> None:
        """Client authenticates using explicit credentials."""
        with Client(
            email=os.environ["RFI_EMAIL"],
            password=os.environ["RFI_PASSWORD"],
        ) as client:
            result = client.questions.list()
            assert result is not None


class TestQuestions:
    """Test questions resource."""

    def test_list_active_questions(self) -> None:
        """List active questions returns results."""
        with Client() as client:
            result = client.questions.list()
            assert result is not None
            assert len(result.questions) > 0

    def test_list_closed_questions(self) -> None:
        """List closed questions returns results."""
        with Client() as client:
            result = client.questions.list(status="closed")
            assert result is not None
            assert len(result.questions) > 0

    def test_get_question(self) -> None:
        """Get a specific question by ID."""
        with Client() as client:
            # First get a question ID from list
            listed = client.questions.list()
            assert listed.questions
            question_id = listed.questions[0].id

            # Get the specific question
            question = client.questions.get(question_id)
            assert question is not None
            assert question.id == question_id
            assert question.name

    def test_question_has_answers(self) -> None:
        """Questions include answer objects with probabilities."""
        with Client() as client:
            listed = client.questions.list()
            question = listed.questions[0]
            assert question.answers is not None
            assert len(question.answers) >= 2
            # Check answer has probability
            answer = question.answers[0]
            assert answer.name
            assert answer.probability is not None

    def test_question_detail_has_description(self) -> None:
        """Individual question has description."""
        with Client() as client:
            listed = client.questions.list()
            q = client.questions.get(listed.questions[0].id)
            assert q.description is not None
            assert len(q.description) > 0


class TestPredictionSets:
    """Test prediction sets resource."""

    def test_list_predictions_for_question(self) -> None:
        """List prediction sets for a question returns results."""
        with Client() as client:
            # Get a question that has predictions
            questions = client.questions.list()
            question_id = questions.questions[0].id

            result = client.prediction_sets.list(question_id=question_id)
            assert result is not None
            assert len(result.prediction_sets) > 0

    def test_prediction_set_has_predictions(self) -> None:
        """Prediction sets include individual predictions."""
        with Client() as client:
            questions = client.questions.list()
            ps_list = client.prediction_sets.list(question_id=questions.questions[0].id)
            assert ps_list.prediction_sets

            ps = ps_list.prediction_sets[0]
            assert ps.predictions is not None
            assert len(ps.predictions) > 0

            pred = ps.predictions[0]
            assert pred.answer_id > 0
            assert 0 <= pred.forecasted_probability <= 1

    def test_prediction_set_has_metadata(self) -> None:
        """Prediction sets include username and timestamps."""
        with Client() as client:
            questions = client.questions.list()
            ps_list = client.prediction_sets.list(question_id=questions.questions[0].id)
            ps = ps_list.prediction_sets[0]
            assert ps.membership_username
            assert ps.created_at is not None


class TestComments:
    """Test comments resource."""

    def test_list_comments(self) -> None:
        """List comments returns results."""
        with Client() as client:
            questions = client.questions.list()
            question_id = questions.questions[0].id

            result = client.comments.list(
                commentable_id=question_id,
                commentable_type="Forecast::Question",
            )
            assert result is not None
            # Comments may or may not exist for every question
            assert isinstance(result.comments, list)


class TestPagination:
    """Test pagination."""

    def test_different_pages_return_different_results(self) -> None:
        """Page 1 and page 2 return different questions."""
        with Client() as client:
            page1 = client.questions.list(status="all", page=1)
            page2 = client.questions.list(status="all", page=2)

            if page1.questions and page2.questions:
                ids1 = {q.id for q in page1.questions}
                ids2 = {q.id for q in page2.questions}
                assert len(ids1 & ids2) == 0


class TestBacktesting:
    """Test cutoff_date filtering for backtesting."""

    def test_cutoff_date_filters_questions(self) -> None:
        """Older cutoff dates return fewer questions."""
        with Client() as client:
            recent = client.questions.list(cutoff_date="2026-02-14")
            older = client.questions.list(cutoff_date="2025-01-01")

            assert len(recent.questions) >= len(older.questions)

    def test_cutoff_date_filters_predictions(self) -> None:
        """Older cutoff dates return fewer predictions."""
        with Client() as client:
            questions = client.questions.list()
            qid = questions.questions[0].id

            recent = client.prediction_sets.list(
                question_id=qid, cutoff_date="2026-12-31"
            )
            older = client.prediction_sets.list(
                question_id=qid, cutoff_date="2025-01-01"
            )

            assert len(recent.prediction_sets) >= len(older.prediction_sets)


class TestAsyncClient:
    """Test async client parity."""

    @pytest.mark.asyncio
    async def test_async_list_questions(self) -> None:
        """Async client lists questions."""
        async with AsyncClient() as client:
            result = await client.questions.list()
            assert result is not None
            assert len(result.questions) > 0

    @pytest.mark.asyncio
    async def test_async_get_question(self) -> None:
        """Async client gets question detail."""
        async with AsyncClient() as client:
            listed = await client.questions.list()
            q = await client.questions.get(listed.questions[0].id)
            assert q.id == listed.questions[0].id

    @pytest.mark.asyncio
    async def test_async_list_predictions(self) -> None:
        """Async client lists predictions."""
        async with AsyncClient() as client:
            questions = await client.questions.list()
            ps = await client.prediction_sets.list(question_id=questions.questions[0].id)
            assert ps is not None
