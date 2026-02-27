"""Tests for RFI SDK resource classes using DispatchRecorder."""

from __future__ import annotations

from typing import Any

import pytest

from sdk_rfi import Client
from sdk_rfi._utils import _resolve_cutoff_date
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

    def test_list_questions_includes_created_before_with_cutoff(self, client: Client, mock_questions_data: list[dict[str, Any]]) -> None:
        """list(cutoff_date=...) includes created_before param for backtesting."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        client.questions.list(cutoff_date="2025-06-01")

        assert "created_before=2025-06-01" in recorder.last_endpoint

    def test_list_questions_no_cutoff_no_created_before(self, client: Client, mock_questions_data: list[dict[str, Any]]) -> None:
        """list() without cutoff_date does not add created_before (forward testing no-op)."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        client.questions.list()

        assert "created_before=" not in recorder.last_endpoint

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

    def test_list_includes_created_before_with_cutoff(self, client: Client, mock_prediction_sets_data: list[dict[str, Any]]) -> None:
        """list(cutoff_date=...) includes created_before param for backtesting."""
        recorder = DispatchRecorder(body=mock_prediction_sets_data)
        client._base_client._dispatch = recorder

        client.prediction_sets.list(question_id=1001, cutoff_date="2025-06-01")

        assert "created_before=2025-06-01" in recorder.last_endpoint

    def test_list_no_cutoff_no_created_before(self, client: Client, mock_prediction_sets_data: list[dict[str, Any]]) -> None:
        """list() without cutoff_date does not add created_before (forward testing no-op)."""
        recorder = DispatchRecorder(body=mock_prediction_sets_data)
        client._base_client._dispatch = recorder

        client.prediction_sets.list(question_id=1001)

        assert "created_before=" not in recorder.last_endpoint


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


class TestResolveCutoffDate:
    """Test the _resolve_cutoff_date helper."""

    def test_returns_none_by_default(self) -> None:
        """No env var + no param = None (forward testing no-op)."""
        assert _resolve_cutoff_date() is None
        assert _resolve_cutoff_date(None) is None

    def test_returns_parameter_when_set(self) -> None:
        """Parameter is returned when no env var is set."""
        assert _resolve_cutoff_date("2025-01-01") == "2025-01-01"

    def test_env_var_overrides_parameter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CUTOFF_DATE env var always overrides the parameter."""
        monkeypatch.setenv("CUTOFF_DATE", "2024-06-15")
        assert _resolve_cutoff_date("2099-12-31") == "2024-06-15"
        assert _resolve_cutoff_date(None) == "2024-06-15"
        assert _resolve_cutoff_date() == "2024-06-15"

    def test_empty_env_var_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty CUTOFF_DATE env var is treated as unset."""
        monkeypatch.setenv("CUTOFF_DATE", "")
        assert _resolve_cutoff_date() is None
        assert _resolve_cutoff_date("2025-01-01") == "2025-01-01"


class TestCutoffDateQuestions:
    """Test cutoff_date filtering on Questions resource."""

    def test_cutoff_filters_questions_by_published_at(self, client: Client) -> None:
        """Questions published after cutoff are excluded."""
        mock_data = [
            {
                "id": 1,
                "name": "Old question",
                "published_at": "2024-01-01T12:00:00.000Z",
                "created_at": "2024-01-01T08:00:00.000Z",
                "answers": [],
            },
            {
                "id": 2,
                "name": "Future question",
                "published_at": "2026-06-01T12:00:00.000Z",
                "created_at": "2026-06-01T08:00:00.000Z",
                "answers": [],
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.questions.list(cutoff_date="2025-01-01")

        assert len(result.questions) == 1
        assert result.questions[0].id == 1

    def test_no_cutoff_returns_all(self, client: Client) -> None:
        """Without cutoff, all questions are returned (no filtering)."""
        mock_data = [
            {
                "id": 1,
                "name": "Old question",
                "published_at": "2024-01-01T12:00:00.000Z",
                "created_at": "2024-01-01T08:00:00.000Z",
                "answers": [],
            },
            {
                "id": 2,
                "name": "Future question",
                "published_at": "2026-06-01T12:00:00.000Z",
                "created_at": "2026-06-01T08:00:00.000Z",
                "answers": [],
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.questions.list()

        assert len(result.questions) == 2

    def test_env_var_overrides_cutoff_param(self, client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
        """CUTOFF_DATE env var overrides the cutoff_date parameter."""
        mock_data = [
            {
                "id": 1,
                "name": "Old question",
                "published_at": "2024-01-01T12:00:00.000Z",
                "created_at": "2024-01-01T08:00:00.000Z",
                "answers": [],
            },
            {
                "id": 2,
                "name": "Future question",
                "published_at": "2026-06-01T12:00:00.000Z",
                "created_at": "2026-06-01T08:00:00.000Z",
                "answers": [],
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        # Parameter says far future, but env var says early cutoff
        monkeypatch.setenv("CUTOFF_DATE", "2025-01-01")
        result = client.questions.list(cutoff_date="2099-12-31")

        assert len(result.questions) == 1
        assert result.questions[0].id == 1
        # Verify endpoint uses env var date, not the param
        assert "created_before=2025-01-01" in recorder.last_endpoint

    def test_get_returns_none_after_cutoff(self, client: Client) -> None:
        """get() returns None if question was published after cutoff."""
        mock_data = {
            "id": 1,
            "name": "Future question",
            "published_at": "2026-06-01T12:00:00.000Z",
            "created_at": "2026-06-01T08:00:00.000Z",
            "answers": [],
        }
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.questions.get(1, cutoff_date="2025-01-01")

        assert result is None

    def test_get_returns_question_before_cutoff(self, client: Client) -> None:
        """get() returns question if published before cutoff."""
        mock_data = {
            "id": 1,
            "name": "Old question",
            "published_at": "2024-01-01T12:00:00.000Z",
            "created_at": "2024-01-01T08:00:00.000Z",
            "answers": [],
        }
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.questions.get(1, cutoff_date="2025-01-01")

        assert result is not None
        assert result.id == 1

    def test_get_no_cutoff_returns_question(self, client: Client) -> None:
        """get() without cutoff always returns the question."""
        mock_data = {
            "id": 1,
            "name": "Future question",
            "published_at": "2099-01-01T12:00:00.000Z",
            "created_at": "2099-01-01T08:00:00.000Z",
            "answers": [],
        }
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.questions.get(1)

        assert result is not None
        assert result.id == 1


class TestCutoffDatePredictionSets:
    """Test cutoff_date filtering on PredictionSets resource."""

    def test_cutoff_filters_predictions(self, client: Client) -> None:
        """Prediction sets created after cutoff are excluded."""
        mock_data = [
            {
                "id": 1,
                "membership_username": "user1",
                "created_at": "2024-01-15T10:00:00.000Z",
                "updated_at": "2024-01-15T10:00:00.000Z",
                "predictions": [],
            },
            {
                "id": 2,
                "membership_username": "user2",
                "created_at": "2026-06-01T10:00:00.000Z",
                "updated_at": "2026-06-01T10:00:00.000Z",
                "predictions": [],
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.prediction_sets.list(question_id=1, cutoff_date="2025-01-01")

        assert len(result.prediction_sets) == 1
        assert result.prediction_sets[0].id == 1

    def test_no_cutoff_returns_all(self, client: Client) -> None:
        """Without cutoff, all prediction sets are returned."""
        mock_data = [
            {
                "id": 1,
                "membership_username": "user1",
                "created_at": "2024-01-15T10:00:00.000Z",
                "updated_at": "2024-01-15T10:00:00.000Z",
                "predictions": [],
            },
            {
                "id": 2,
                "membership_username": "user2",
                "created_at": "2026-06-01T10:00:00.000Z",
                "updated_at": "2026-06-01T10:00:00.000Z",
                "predictions": [],
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.prediction_sets.list(question_id=1)

        assert len(result.prediction_sets) == 2

    def test_env_var_overrides_cutoff_param(self, client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
        """CUTOFF_DATE env var overrides cutoff_date parameter for predictions."""
        mock_data = [
            {
                "id": 1,
                "membership_username": "user1",
                "created_at": "2024-01-15T10:00:00.000Z",
                "updated_at": "2024-01-15T10:00:00.000Z",
                "predictions": [],
            },
            {
                "id": 2,
                "membership_username": "user2",
                "created_at": "2026-06-01T10:00:00.000Z",
                "updated_at": "2026-06-01T10:00:00.000Z",
                "predictions": [],
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        monkeypatch.setenv("CUTOFF_DATE", "2025-01-01")
        result = client.prediction_sets.list(question_id=1, cutoff_date="2099-12-31")

        assert len(result.prediction_sets) == 1
        assert result.prediction_sets[0].id == 1
        assert "created_before=2025-01-01" in recorder.last_endpoint


class TestCutoffDateComments:
    """Test cutoff_date filtering on Comments resource."""

    def test_cutoff_filters_comments(self, client: Client) -> None:
        """Comments created after cutoff are excluded."""
        mock_data = [
            {
                "id": 1,
                "content": "Old comment",
                "membership_username": "user1",
                "created_at": "2024-01-15T10:00:00.000Z",
                "updated_at": "2024-01-15T10:00:00.000Z",
            },
            {
                "id": 2,
                "content": "Future comment",
                "membership_username": "user2",
                "created_at": "2026-06-01T10:00:00.000Z",
                "updated_at": "2026-06-01T10:00:00.000Z",
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.comments.list(
            commentable_id=1,
            commentable_type="Forecast::Question",
            cutoff_date="2025-01-01",
        )

        assert len(result.comments) == 1
        assert result.comments[0].id == 1

    def test_no_cutoff_returns_all(self, client: Client) -> None:
        """Without cutoff, all comments are returned."""
        mock_data = [
            {
                "id": 1,
                "content": "Old comment",
                "membership_username": "user1",
                "created_at": "2024-01-15T10:00:00.000Z",
                "updated_at": "2024-01-15T10:00:00.000Z",
            },
            {
                "id": 2,
                "content": "Future comment",
                "membership_username": "user2",
                "created_at": "2026-06-01T10:00:00.000Z",
                "updated_at": "2026-06-01T10:00:00.000Z",
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        result = client.comments.list(
            commentable_id=1,
            commentable_type="Forecast::Question",
        )

        assert len(result.comments) == 2

    def test_env_var_overrides_cutoff_param(self, client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
        """CUTOFF_DATE env var overrides cutoff_date parameter for comments."""
        mock_data = [
            {
                "id": 1,
                "content": "Old comment",
                "membership_username": "user1",
                "created_at": "2024-01-15T10:00:00.000Z",
                "updated_at": "2024-01-15T10:00:00.000Z",
            },
            {
                "id": 2,
                "content": "Future comment",
                "membership_username": "user2",
                "created_at": "2026-06-01T10:00:00.000Z",
                "updated_at": "2026-06-01T10:00:00.000Z",
            },
        ]
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        monkeypatch.setenv("CUTOFF_DATE", "2025-01-01")
        result = client.comments.list(
            commentable_id=1,
            commentable_type="Forecast::Question",
            cutoff_date="2099-12-31",
        )

        assert len(result.comments) == 1
        assert result.comments[0].id == 1
        assert "created_before=2025-01-01" in recorder.last_endpoint
