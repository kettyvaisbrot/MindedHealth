Data models / migrations
Task: Define chat data models
Design tables/entities for:
ChatMessage (id, user_id, room_type, pseudonym, content, timestamp, chat_day).
PseudonymAssignment (user_id, room_type, chat_day, pseudonym, created_at).
MuteBan (user_id, type [mute/ban], active, scope [global], starts_at, ends_at, reason, created_by).
SafetyFlag (id, message_id, user_id, room_type, created_at, reason/type).
AuditLog (id, admin_user_id, target_user_id, action_type, details, created_at).
Acceptance criteria:
Schema supports the (user_id, room_type, chat_day) → pseudonym mapping with uniqueness per room/day.
ChatMessage can be queried by room_type + chat_day with pagination.
Mutes/bans can be checked by user_id quickly.
Safety flags and audit logs can be written without schema changes.
Task: Implement DB migrations
Create migrations for all chat-related tables and indexes.
Add appropriate indexes on:
ChatMessage(room_type, chat_day, created_at).
PseudonymAssignment(user_id, room_type, chat_day) and (room_type, chat_day, pseudonym) for uniqueness.
MuteBan(user_id, active) and SafetyFlag(message_id, user_id).
Acceptance criteria:
Migrations run successfully on dev/staging DB.
Uniqueness constraints enforce:
One pseudonym per user/room/day.
No duplicate pseudonyms per room/day.
Query plans show index usage for main message history query.
WebSocket layer
Task: Implement authenticated WebSocket endpoint
Add WS endpoint for chat that:
Authenticates using existing app auth (session or JWT).
Validates user role against requested room_type.
Checks for active bans before accepting connection.
Acceptance criteria:
Unauthenticated requests are rejected with UNAUTHORIZED.
Authenticated users with wrong role get FORBIDDEN_ROOM.
Banned users get a clear BANNED error and are disconnected.
Valid users connect and stay connected.
Task: Implement message send & broadcast flow
Define a send_message event:
Validate payload.
Resolve pseudonym (via PseudonymAssignment).
Run moderation/filters and rate limits (stubs or real implementations).
Persist allowed messages in ChatMessage.
Broadcast to all connections in the same room on this node.
Acceptance criteria:
A valid message from one user appears to all other users in same room_type with correct pseudonym and timestamp.
Blocked messages do not appear to any other users.
Connection routing works correctly for multiple clients on same node.
Task: Implement history loading within current day
Implement a load_history or initial-history fetch:
Fetch paginated messages for room_type + current chat_day, ordered consistently.
Acceptance criteria:
On connect, client can request and receive the last N (configurable) messages of the current day.
Pagination returns correct next/previous sets without duplicates or gaps.
History never includes messages from past chat days.
Task: Handle auth expiry and role changes mid-connection
Periodically (or on activity) verify session/token is still valid.
If user role changes or session is invalidated, close the WS.
Acceptance criteria:
When a user logs out elsewhere, the chat connection is closed within a reasonable interval.
If a user’s role is changed to one that cannot access the room, the connection drops and future sends are rejected.
Moderation & PII filtering
Task: Implement content filters (abuse, PII, links)
Implement a filter pipeline for incoming message content:
Word/phrase lists (Hebrew + English) for abusive content.
Regex for emails, phone numbers, and URLs.
Acceptance criteria:
Test phrases with obvious abuse, emails, phone numbers, and URLs are consistently blocked.
Non-abusive, non-PII messages are not falsely blocked in basic test cases.
Task: Integrate filters into message send flow
Wire filters into send_message:
If blocked:
Do not persist message.
Do not broadcast.
Send generic error to sender.
Acceptance criteria:
Sender of a blocked message receives: “Your message was blocked due to community guidelines.”
Blocked messages never appear in ChatMessage table.
Other users never see blocked messages.
Task: Safety flagging for crisis content
Implement a basic crisis keyword list to flag potential self-harm/harm-to-others messages.
On detection, create a SafetyFlag record and send a private/system safety response to the sender.
Acceptance criteria:
Messages containing crisis keywords trigger a SafetyFlag entry.
Sender receives a crisis-help message.
Safety Admin can query flagged messages via admin tools (even if just via a simple internal view).
Rate limiting & bans
Task: Implement per-user message rate limiting
Implement in-memory rate limiting for:
10 messages/minute per user per room.
Acceptance criteria:
A user can send up to the threshold without errors.
Messages beyond the threshold in the same minute window are rejected with a clear rate-limit error.
After the window resets, sending is allowed again.
Task: Implement reconnect rate limiting
Track reconnect attempts per user:
Max 5 reconnects per minute.
Acceptance criteria:
Under normal behavior, reconnects work.
Rapid reconnect loops hit the cap and get a clear error.
After cooldown, the user can connect again.
Task: Implement minimal per-IP limits
Track concurrent connections per IP and enforce a reasonable maximum.
Acceptance criteria:
A single IP can hold multiple normal user connections.
Exceeding the configured cap blocks additional connections from that IP with an error.
Task: Implement mutes and bans enforcement
At connection time and on send:
Check MuteBan for the user.
Muted:
Allow connection.
Reject sends with “You are muted until \<time\>. Reason: guideline violation.”
Banned:
Reject connection attempts entirely.
Acceptance criteria:
Muted users see room activity but cannot send.
Banned users cannot connect.
Unmuting/unbanning via admin tools takes effect immediately on next check.
Daily reset & retention job
Task: Implement chat-day calculation & new-day event
Implement function to derive chat_day from UTC timestamp and Asia/Jerusalem timezone.
At local midnight:
Start using the new chat_day for messages and pseudonyms.
Broadcast new_day_started system event to relevant connections.
Acceptance criteria:
Timestamps just before and after midnight map to different chat_day values.
Connected clients receive a new_day_started event at the correct time.
New messages after midnight are tagged with the new chat_day.
Task: Implement pseudonym rotation at day boundary
Ensure new (user_id, room_type, chat_day) combinations get new pseudonyms.
Old pseudonym assignments are not reused for the same user next day.
Acceptance criteria:
Same user in same room has one stable pseudonym during a day.
After midnight, that user gets a new pseudonym in that room.
No pseudonym collisions within a room/day.
Task: Implement 24-hour retention cleanup
Background job to delete old ChatMessage records (>24h) and any associated secondary logs (mod logs) as needed.
Acceptance criteria:
Messages older than the configured retention window are no longer present in ChatMessage.
Safety flags and related records are either cleaned up in sync (for MVP) or documented if retained separately.
Job can be run periodically without timeouts or major performance issues on expected data volume.
Tests
Task: Unit tests for data model and pseudonym logic
Test:
Pseudonym creation and uniqueness per (user, room, day).
Pseudonym reuse across devices and reconnects.
Correct behavior across day boundaries.
Acceptance criteria:
Tests cover single- and multi-connection scenarios for same user.
Tests verify no duplicate pseudonyms in a given room/day.
Day-change tests confirm pseudonym rotation.
Task: WebSocket and auth flow tests
Test:
Connection acceptance/rejection based on auth and role.
Message send/broadcast path.
Behavior when a user is banned/muted.
Acceptance criteria:
Automated tests simulate clients and verify all major WS flows.
Unauthorized/forbidden/ban cases are correctly rejected.
Task: Moderation & PII filter tests
Tests for:
Abusive phrases in Hebrew/English.
PII detection (emails, phone numbers).
Link detection.
False positive guardrails for benign text.
Acceptance criteria:
Block lists catch all targeted examples.
Non-abusive test messages are allowed.
Blocked messages trigger the expected generic error.
Task: Rate limiting, mutes, and bans tests
Tests for:
Per-user message rate limiting.
Reconnect limit.
Per-IP connection cap.
Mute and ban behavior from both user and admin perspectives.
Acceptance criteria:
Tests demonstrate correct enforcement and reset of rate limits.
Muted users cannot send but can read.
Banned users cannot connect until unbanned.
Task: Daily reset & retention tests
Simulate:
Messages around midnight boundary.
New-day event emission.
Retention job deleting records older than 24 hours.
Acceptance criteria:
Messages from previous chat_day are not returned in history after midnight.
New-day events are emitted at the correct time.
After running the retention job, messages older than the configured window are gone from primary storage.