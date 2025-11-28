# OpenRSVP HTTP API (for the `invite` CLI)

This summarizes the current FastAPI endpoints you can drive from a standalone Typer CLI. All payloads and responses are JSON unless noted.

## Auth Model
- Event admin token: use the string shown in the admin link `/e/{event_id}/admin/{admin_token}` and send it as `Authorization: Bearer <admin_token>`. Root token also works for admin-gated endpoints.
- RSVP token: returned once when a guest submits. Use `Authorization: Bearer <rsvp_token>` for the `.../rsvps/self` endpoints.
- Public endpoints need no auth.

## Event Lifecycle
- `POST /api/v1/events` → create an event. Body:
  - `title` (str, required)
  - `description` (str, optional)
  - `start_time` (ISO str, required)
  - `end_time` (ISO str, optional, must be after start)
  - `timezone_offset_minutes` (int, default 0; used to normalize times to UTC)
  - `location` (str, optional)
  - `channel_name` (str, optional), `channel_visibility` (`public`|`private`, default `public`)
  - `is_private` (bool, default false)
  - `admin_approval_required` (bool, default false; if true, new RSVPs start `pending`)
  - Response `201`: `{ "event": <event>, "admin_token": "<token>" }` where `event.links.admin` contains the admin URL.
- `GET /api/v1/events/{event_id}` → public event detail. Includes only approved, non-private RSVPs and public messages. Also returns `rsvp_counts` (public/private tallies) and `links.public`.
- `PATCH /api/v1/events/{event_id}` (admin bearer) → update any event field above; can move between channels or clear the channel by sending empty `channel_name`. Response: `{ "event": <event> }` with `links.admin`.
- `DELETE /api/v1/events/{event_id}` (admin bearer) → removes the event, `204 No Content`.
- `GET /api/v1/events/{event_id}/rsvps` (admin bearer) → list all RSVPs for the event with tokens and internal IDs. Response: `{ "event": <event>, "rsvps": [<rsvp…>], "stats": {yes_count,…} }`.

## RSVP Flow (guest-facing)
- `POST /api/v1/events/{event_id}/rsvps` → submit RSVP. Body:
  - `name` (str), `attendance_status` (`yes`|`no`|`maybe`), `pronouns` (str, optional),
  - `guest_count` (int, 0–5, default 0), `note` (str, optional), `is_private_rsvp` (bool, default false).
  - Response `201`: `{ "rsvp": <rsvp with rsvp_token>, "links": { "self": "/api/v1/events/{id}/rsvps/self", "html": "/e/{id}/rsvp/{token}" } }`.
- `GET /api/v1/events/{event_id}/rsvps/self` (bearer RSVP token) → returns own RSVP plus attendee-visible messages.
- `PATCH /api/v1/events/{event_id}/rsvps/self` (bearer RSVP token) → update same fields as create; `note` is stored as an attendee message. Response returns updated RSVP with attendee messages.
- `DELETE /api/v1/events/{event_id}/rsvps/self` (bearer RSVP token) → deletes own RSVP, `204`.

## Admin Actions on RSVPs
- `POST /events/{event_id}/rsvps/{rsvp_id}/approve|reject|pending` (admin bearer) → change approval status. Optional body: `{ "reason": "…" }` (used for rejection note). Response: `{ "rsvp": <rsvp with messages> }`.
- `POST /events/{event_id}/rsvps/{rsvp_id}/messages` (admin bearer) → add an internal note or attendee-facing message. Body: `content` (str), `visibility` (`admin`|`attendee`), `message_type` (`admin_note`|`rejection_reason`|`user_note`). Response includes the new message plus the visible message list.
- `DELETE /api/v1/events/{event_id}/rsvps/{rsvp_token}` (admin bearer) → delete an RSVP by token, `204`.

## Event Messages (admin)
- `POST /events/{event_id}/messages` (admin bearer) → add event-level message. Body: `content` (str), `visibility` (`public`|`admin`), `message_type` (`event_update`|`event_internal`). Response: `{ "message": <message> }`.

## Channels
- `GET /api/v1/channels?q=<query>&page=<n>` → list public channels with pagination.
- `GET /api/v1/channels/{slug}?page=<n>` → channel detail + event list. Private channels return all events; public channels only show public events.

## Serialized Shapes (selected)
- `event`: `id`, `title`, `description`, `start_time`, `end_time`, `location`, `is_private`, `admin_approval_required`, `score`, timestamps, optional `channel`, `links.public`, optional `links.admin`, optional `rsvps`, optional `messages`, optional `rsvp_counts` (public/private counts + party sizes).
- `rsvp`: `event_id`, `name`, `pronouns`, `approval_status`/`status`, `attendance_status`, `guest_count`, `is_private`, timestamps, optional `rsvp_token`, optional `id`, optional `messages`.
- `message`: `id`, `event_id`, `rsvp_id`, `author_id`, `message_type`, `visibility`, `content`, `created_at`.
- Stats: `yes|maybe|no_count`, `guest_count`, and `*_total` (count + guests) from `GET /api/v1/events/{event_id}/rsvps`.

## Notes & Defaults
- Time payloads are ISO strings; `timezone_offset_minutes` adjusts incoming times to UTC server storage.
- Attendance statuses outside `yes`/`no`/`maybe` normalize to `maybe`. Approval statuses are `approved`/`pending`/`rejected`; if `admin_approval_required` is true, new RSVPs start `pending`.
- Guest counts are clamped to 0–5. Private RSVPs are hidden from public listings but counted in `rsvp_counts.private`.
