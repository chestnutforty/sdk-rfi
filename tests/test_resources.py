"""Tests for RFI SDK resource classes using DispatchRecorder."""

from __future__ import annotations

from typing import Any

import pytest

from sdk_rfi import Client
from tests.conftest import DispatchRecorder


class TestQuestions:
    """Test the Questions resource."""

    def test_list_questions(self, client: Client, mock_questions_data: list[dict[str, Any]]) -> None:
        """list() returns a QuestionList with parsed questions."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        result = client.questions.list()

        assert recorder.called
        assert len(result.questions) == 1
        assert result.questions[0].id == 1001
        assert result.questions[0].name == "Will X happen by 2026?"

    def test_list_questions_with_status_filter(self, client: Client, mock_questions_data: list[dict[str, Any]]) -> None:
        """list(status=...) includes status in the endpoint."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        client.questions.list(status="closed")

        assert "status=closed" in recorder.last_endpoint

    def test_list_questions_includes_created_before(self, client: Client, mock_questions_data: list[dict[str, Any]]) -> None:
        """list() always includes created_before param (for backtesting cutoff)."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        client.questions.list()

        assert "created_before=" in recorder.last_endpoint

    def test_list_questions_with_pagination(self, client: Client, mock_questions_data: list[dict[str, Any]]) -> None:
        """list(page=...) passes page parameter."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        result = client.questions.list(page=2)

        assert "page=2" in recorder.last_endpoint
        assert result.page == 2

    def test_get_question(self, client: Client, mock_question_data: dict[str, Any]) -> None:
        """get(id) returns a parsed Question."""
        recorder = DispatchRecorder(body=mock_question_data)
        client._base_client._dispatch = recorder

        question = client.questions.get(1001)

        assert recorder.called
        assert question.id == 1001
        assert question.name == "Will X happen by 2026?"
        assert "/api/v1/questions/1001" in recorder.last_endpoint

    def test_question_has_answers(self, client: Client, mock_question_data: dict[str, Any]) -> None:
        """Question includes parsed Answer objects."""
        recorder = DispatchRecorder(body=mock_question_data)
        client._base_client._dispatch = recorder

        question = client.questions.get(1001)

        assert question.answers is not None
        assert len(question.answers) == 2
        assert question.answers[0].name == "Yes"
        assert question.answers[0].probability == 0.65

    def test_list_questions_dict_response(self, client: Client) -> None:
        """list() handles dict response format with 'questions' key."""
        mock_dict = {
            "questions": [
                {
                    "id": 2001,
                    "name": "Test question",
                    "created_at": "2025-01-01T00:00:00.000Z",
                    "published_at": "2025-01-01T00:00:00.000Z",
                    "answers": [],
                }
            ]
        }
        recorder = DispatchRecorder(body=mock_dict)
        client._base_client._dispatch = recorder

        result = client.questions.list()

        assert len(result.questions) == 1
        assert result.questions[0].id == 2001


class TestPredictionSets:
    """Test the PredictionSets resource."""

    def test_list_predictions(self, client: Client, mock_prediction_sets_data: list[dict[str, Any]]) -> None:
        """list(question_id=...) returns parsed prediction sets."""
        recorder = DispatchRecorder(body=mock_prediction_sets_data)
        client._base_client._dispatch = recorder

        result = client.prediction_sets.list(question_id=1001)

        assert recorder.called
        assert len(result.prediction_sets) == 1
        assert result.prediction_sets[0].id == 5001
        assert "question_id=1001" in recorder.last_endpoint

    def test_prediction_set_has_predictions(self, client: Client, mock_prediction_sets_data: list[dict[str, Any]]) -> None:
        """Prediction sets include parsed Prediction objects."""
        recorder = DispatchRecorder(body=mock_prediction_sets_data)
        client._base_client._dispatch = recorder

        result = client.prediction_sets.list(question_id=1001)
        ps = result.prediction_sets[0]

        assert ps.predictions is not None
        assert len(ps.predictions) == 1
        assert ps.predictions[0].answer_id == 2001
        assert ps.predictions[0].forecasted_probability == 0.72

    def test_prediction_set_metadata(self, client: Client, mock_prediction_sets_data: list[dict[str, Any]]) -> None:
        """Prediction sets include username and timestamps."""
        recorder = DispatchRecorder(body=mock_prediction_sets_data)
        client._base_client._dispatch = recorder

        result = client.prediction_sets.list(question_id=1001)
        ps = result.prediction_sets[0]

        assert ps.membership_username == "forecaster1"
        assert ps.created_at is not None

    def test_list_includes_created_before(self, client: Client, mock_prediction_sets_data: list[dict[str, Any]]) -> None:
        """list() always includes created_before param (for backtesting)."""
        recorder = DispatchRecorder(body=mock_prediction_sets_data)
        client._base_client._dispatch = recorder

        client.prediction_sets.list(question_id=1001)

        assert "created_before=" in recorder.last_endpoint


class TestComments:
    """Test the Comments resource."""

    def test_list_comments(self, client: Client, mock_comments_data: list[dict[str, Any]]) -> None:
        """list() returns parsed comments."""
        recorder = DispatchRecorder(body=mock_comments_data)
        client._base_client._dispatch = recorder

        result = client.comments.list(
            commentable_id=1001,
            commentable_type="Forecast::Question",
        )

        assert recorder.called
        assert len(result.comments) == 1
        assert result.comments[0].id == 8001
        assert "commentable_id=1001" in recorder.last_endpoint

    def test_comment_content(self, client: Client, mock_comments_data: list[dict[str, Any]]) -> None:
        """Comments have content and metadata."""
        recorder = DispatchRecorder(body=mock_comments_data)
        client._base_client._dispatch = recorder

        result = client.comments.list(commentable_id=1001, commentable_type="Forecast::Question")
        comment = result.comments[0]

        assert comment.content is not None
        assert comment.membership_username == "forecaster1"
        assert comment.created_at is not None

    def test_empty_comments(self, client: Client) -> None:
        """list() handles empty list response."""
        recorder = DispatchRecorder(body=[])
        client._base_client._dispatch = recorder

        result = client.comments.list(commentable_id=9999, commentable_type="Forecast::Question")

        assert len(result.comments) == 0
