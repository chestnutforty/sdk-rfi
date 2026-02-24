# RAND Forecasting Initiative (RFI) -- Complete Method Reference

> Auto-generated from SDK introspection. 4 methods across 3 resources.

## comments

### `client.comments.list(commentable_id=None, commentable_type=None, page=None, created_before=None, created_after=None, cutoff_date=...)`

List comments.

Filter by the ID of the commented object (e.g., question ID) and by type (e.g., 'Forecast::Question'). Supports pagination and date range filtering.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| commentable_id | int or None | no | None | Filter by the ID of the commented object (e.g., question ID) |
| commentable_type | str or None | no | None | Filter by type (e.g., 'Forecast::Question') |
| page | int or None | no | None | Page number for pagination |
| created_before | str or None | no | None | ISO8601 date |
| created_after | str or None | no | None | ISO8601 date |
| cutoff_date | str | no | today | Filter to comments made before this date (YYYY-MM-DD) |

**Returns:** `CommentList`

---

## prediction_sets

### `client.prediction_sets.list(question_id=None, membership_id=None, filter=None, page=None, created_before=None, created_after=None, updated_before=None, updated_after=None, cutoff_date=...)`

List prediction sets (forecasts). Only returns forecasts made before cutoff_date.

Each prediction set contains one or more individual predictions (one per answer) along with the forecaster's username and optional rationale text.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| question_id | int or None | no | None | Filter by question ID |
| membership_id | int or None | no | None | Filter by membership (user) ID |
| filter | str or None | no | None | 'comments_with_links' or 'comments_following' |
| page | int or None | no | None | Page number for pagination |
| created_before | str or None | no | None | ISO8601 date |
| created_after | str or None | no | None | ISO8601 date |
| updated_before | str or None | no | None | ISO8601 date |
| updated_after | str or None | no | None | ISO8601 date |
| cutoff_date | str | no | today | Filter to forecasts made before this date (YYYY-MM-DD) |

**Returns:** `PredictionSetList`

---

## questions

### `client.questions.get(question_id, cutoff_date=...)`

Get a single question by ID. Returns the full question object including answers with crowd probabilities, description, resolution notes, and metadata.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| question_id | int | yes | -- | The question ID |
| cutoff_date | str | no | today | Filter to data available as of this date (YYYY-MM-DD) |

**Returns:** `Question`

---

### `client.questions.list(status=None, tags=None, challenges=None, sort=None, filter=None, ids=None, page=None, created_before=None, created_after=None, updated_before=None, updated_after=None, include_tag_ids=None, cutoff_date=...)`

List forecasting questions. Returns paginated question objects with answers and crowd probabilities.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| status | str or None | no | None | Filter by status - 'closed', 'all', or omit for active only |
| tags | str or None | no | None | Comma-separated tags to filter by |
| challenges | str or None | no | None | Comma-separated challenge IDs |
| sort | str or None | no | None | Sort by 'published_at', 'ends_at', 'resolved_at', or 'prediction_sets_count' |
| filter | str or None | no | None | 'starred' or 'featured' |
| ids | str or None | no | None | Comma-separated question IDs |
| page | int or None | no | None | Page number for pagination |
| created_before | str or None | no | None | ISO8601 date - only questions created before this date |
| created_after | str or None | no | None | ISO8601 date - only questions created after this date |
| updated_before | str or None | no | None | ISO8601 date |
| updated_after | str or None | no | None | ISO8601 date |
| include_tag_ids | bool or None | no | None | Include tag IDs in response |
| cutoff_date | str | no | today | Filter to data available as of this date (YYYY-MM-DD) |

**Returns:** `QuestionList`
