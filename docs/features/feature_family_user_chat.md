Family and User Anonymous Chat – MVP Feature Specification (Updated)
1. Overview
Implement two anonymous, WebSockets-based group chat rooms within MindedHealth:
Patient Room: For authenticated users with role patient.
Family/Partner Room: For authenticated users with role family/partner.
Constraints for MVP:
Scale: ~200 concurrent users total (per room, roughly).
Deployment: Single application node.
Audience: Internal / early-stage product (still privacy- and safety-conscious).
Core principles:
Anonymity for participants (pseudonyms only).
Safety via automated moderation and rate limits.
Day-bounded visibility (no cross-day history in the UI).
Minimal, auditable internal access for safety investigations.

2. Roles, Permissions & Access Control
2.1 User & staff roles
Patient
May access only the Patient Room.
Family/Partner
May access only the Family/Partner Room.
(Future) If an account has both roles, it may access both rooms; see pseudonym rules in §3.
Clinician/Therapist
No access to chat messages or live rooms.
Admin (standard)
No access to chat content; no special chat rights.
Safety Admin
Can:
View retained chat messages via internal/admin tools.
Map pseudonyms/messages → underlying user account for safety emergencies and abuse investigations only.
Apply/remove mutes and bans (see §6.3).
Must operate through authenticated internal tools; all actions are audited (§7.3).
2.2 Room access rules
Only authenticated users may open a WebSocket connection.
Access depends on role → room_type:
patient → PATIENT_ROOM
family/partner → FAMILY_ROOM
If a user’s role changes (e.g., family → patient) while connected:
Existing WebSocket connections must be terminated promptly on the server side.
Subsequent connection attempts must respect the new role-based access.

3. Pseudonym & Identity Model
3.1 Pseudonym scope and stability
Key rule: Pseudonym is stable per (user_id, room_type, chat_day).
For a given user, room, and day:
All connections (including multiple devices) share the same pseudonym.
Disconnects/reconnects do not change the pseudonym.
Pseudonym is regenerated when:
The chat day changes (§4), or
The user joins a different room_type (if they ever have both roles).
3.2 Uniqueness constraints
Within a given room_type + chat_day:
No two users may share the same pseudonym.
Enforced via a persisted mapping table and conflict-safe generation logic.
Pseudonyms may be reused across different days and/or different rooms, but:
Never reuse the same pseudonym across rooms for the same user on the same day.
3.3 Cross-room separation
If a user can access both rooms (future scenario):
PATIENT_ROOM pseudonym and FAMILY_ROOM pseudonym for that user must be different each day.
No intentional linkage between room pseudonyms on the client side.
3.4 Internal identity mapping
Store:
Pseudonym ↔ (user_id, room_type, chat_day) mapping in a secured table.
Only Safety Admin tools may reveal this mapping, and only:
For active safety emergencies or abuse investigations.

4. Day Boundary, Timezone & History
4.1 Chat day definition
Chat day:
Defined using timezone Asia/Jerusalem.
Implemented as:
Store timestamps in UTC in DB.
Convert to/from Asia/Jerusalem when determining the chat day boundary.
Time source:
Use a reliable server-side clock (e.g., system time synced via NTP).
DST:
Handle daylight-saving transitions according to official rules for Asia/Jerusalem (i.e., rely on underlying tz database).
4.2 Day rollover behavior
At local midnight in Asia/Jerusalem:
Server logically starts a new chat day for each room.
New messages are associated with the new chat_day.
Previously stored messages remain persisted up to retention limits (§5) but are no longer served to clients.
WebSocket behavior:
Existing connections may stay open.
Server sends a system event over WS:
system event with { type: "new_day_started", room_type, timestamp }.
Clients are expected to:
Clear their local message list.
Optionally display a system message like “A new day has started”.
4.3 History visibility (MVP decision)
MVP behavior (must-fix decision):
On connect (or on “load history”):
User may see all messages from the current chat_day, not just from connection time.
History must be paginated:
Define a page size (e.g., 50 messages per page, configurable).
Newer messages first or last (define order and keep consistent).
Across days:
Users cannot access messages from previous chat days, even if still retained server-side.

5. Data Retention & Deletion
5.1 User-visible vs server-side retention
UI:
Users see only current chat_day messages.
Server:
Messages (including content) are stored in chat tables for 24 hours from their creation time.
After ~24 hours:
Messages are deleted from primary storage as part of a scheduled cleanup.
5.2 Safety-flagged messages
MVP alignment:
Safety-flagged messages follow the same 24-hour deletion policy as other messages.
This keeps behavior simple for early-stage internal use.
Future change:
Spec explicitly allows revisiting this for longer retention if needed; see §10.
5.3 Backups & retention statement
Backups:
Chat data may persist in encrypted backups beyond 24 hours.
Backups are:
Used only for disaster recovery.
Not directly queryable by standard application features or Safety Admin tools.
Retention statement:
Product copy and internal docs should clearly reflect that:
Messages are removed from live systems after ~24 hours, but
May exist in backups for a longer, fixed period (e.g., per standard backup policy).

6. Content, Moderation & Abuse Handling
6.1 Allowed & disallowed content (MVP)
Allowed:
Text-only messages, including emojis.
Disallowed:
Images, files, any other attachments.
Links/URLs:
Detect with regex; block such messages.
PII patterns:
Phone numbers (basic international and local formats).
Email addresses (standard regex).
6.2 Automated moderation (MVP)
Filters:
Configurable list of blocked words/phrases (Hebrew + English).
Basic regex patterns for abusive content and disallowed PII/links.
Behavior:
Each incoming message is checked server-side before:
Storage as a chat message.
Broadcast to other clients.
If the content:
Contains abusive terms, or
Contains disallowed links or obvious PII,
Then:
Do not broadcast to others.
Do not store as a normal chat message.
Optionally store in a separate moderation log/structure for internal review (also 24h max retention in MVP).
User feedback (MVP decision):
For any server-side block (abusive language, PII, links):
Sender receives an error message:
“Your message was blocked due to community guidelines.”
We intentionally reuse this generic text in MVP for simplicity.
6.3 Rate limiting & abuse prevention
Message rate limit
Max 10 messages per minute per user per room.
Implementation:
Use a simple sliding window or token bucket in memory on the single node.
When exceeded:
Reject additional messages until the rate falls below the threshold.
Respond with a clear error (e.g., “You are sending messages too quickly. Please slow down.”).
Reconnect limit
Max 5 reconnect attempts per minute per user.
When exceeded:
Temporarily reject new WS connections for that user for a short window (e.g., 1–5 minutes).
Return an error message indicating excessive reconnects.
Per-IP protections (minimal MVP)
Implement simple per-IP caps, e.g.:
Max number of concurrent connections from a single IP (configurable).
Enough to prevent trivial abuse in an internal environment; does not need to be fully distributed.
6.4 Mutes and bans
Scope:
Mutes and bans are applied at the account level, not pseudonym level.
For MVP, they are global across all chat rooms:
If a user is muted, they are muted in both Patient and Family rooms (if they had access).
Same for bans.
Mute behavior
Muted users:
Remain able to connect and see messages.
Cannot successfully send messages:
Server drops their messages (not broadcast, not stored as normal chat).
Returns error:
“You are muted until \<time\>. Reason: guideline violation.”
Ban behavior
Banned users:
Cannot connect to chat WebSocket at all.
Connection attempts yield an error like:
“You are currently not allowed to access the chat due to guideline violations.”
Control:
Only Safety Admin can:
Apply or remove mutes.
Apply or remove bans.
All such actions are logged in the audit log (§7.3).

7. Safety & Crisis Handling
7.1 Safety event detection
Messages may be heuristically detected as indicating:
Imminent self-harm.
Harm to others.
MVP may use:
Keyword-based and regex-based detection, similar to moderation filters, but tuned for crisis keywords.
7.2 User-facing response for safety content
If a message is classified as a potential safety crisis:
The system:
Sends a private/system message back to the sender (not visible to others) with:
Crisis resources (e.g., hotline text; configurable).
Clear guidance to contact emergency services in case of immediate danger.
The original message may still be:
Stored and visible in the room as per normal rules, OR
Optionally blocked, depending on product decision (MVP: can be stored and visible unless also abusive).
7.3 Internal safety flags & de-anonymization
Safety flag:
Create a safety flag record when a message is detected as a safety concern, containing:
Message ID.
Timestamp.
Room type.
Pseudonym.
User ID.
Access:
Only Safety Admin tools can view safety flags and linked content.
De-anonymization:
Safety Admin may map flagged messages to the underlying user account only for:
Safety emergencies.
Abuse investigations.
Audit:
Every access to safety flags and de-anonymization action is written to an audit log:
Who (Safety Admin user_id).
When (timestamp).
What (message_id / user_id).
Action type (view, mute, ban, de-anonymize).

8. WebSocket API & Auth (MVP)
8.1 Authentication
WebSocket connection uses the same authentication mechanism as the main app:
For example, session cookie or JWT (decision must match current platform).
Requirements:
On WS connect:
Verify the session/token is valid and not expired.
Verify the user’s role matches the requested room_type.
Mid-connection:
If the underlying session or token is revoked/expired:
Server should close the WebSocket at the next convenient check (e.g., on ping/pong or next message).
If auth depends on cookies:
Enforce Origin checks:
Only allow connections from approved front-end origins.
Optionally use Sec-WebSocket-Protocol or similar to further bind context.
8.2 Core events (conceptual)
Client → Server:
send_message:
{ room_type, content, client_message_id? }
(Optional for MVP) load_history:
{ room_type, page, page_size }
Server → Client:
message:
{ message_id, room_type, pseudonym, content, timestamp }
system:
{ type: "new_day_started", room_type, timestamp }
Possibly other info messages as needed.
error:
{ code, message }, where code may include:
UNAUTHORIZED, FORBIDDEN_ROOM, RATE_LIMITED, MUTED, BANNED, BLOCKED_CONTENT, etc.

9. Logging, Audit & Observability (MVP)
9.1 Application logs
Log metadata only, no message content:
Timestamps.
User ID (internal).
Room type.
Message ID.
Moderation outcome (allowed/blocked/flagged).
Connection events (connect, disconnect, reconnect).
Do not log the actual message text in application logs.
9.2 Chat storage
Message content is stored:
Only in the chat tables/storage.
Subject to 24h retention and cleanup.
9.3 Audit logs
Maintain a separate audit log for:
Safety Admin operations:
Viewing chat messages via admin tools.
Viewing safety-flagged items.
De-anonymizing pseudonyms to user IDs.
Applying/removing mutes and bans.
Properties:
Append-only in practice (no in-place edits).
Stored separately from normal application logs.
9.4 Minimal metrics
At minimum, expose:
messages_per_minute_per_room.
blocked_message_count (per room).
active_connections_per_room.
error_count and reconnect_count.
Used for basic health checks and internal monitoring at small scale.

10. Privacy & Metadata
Client-visible identity
Clients see only:
Pseudonym.
Message content.
Timestamp.
Room type.
Metadata stored
For each message:
user_id (internal).
Pseudonym.
room_type.
Timestamp.
IP address:
Stored only in security logs for up to 7 days.
Used for abuse detection and security monitoring.
User communication
Internal documentation and any user-facing copy must clarify:
Chat is “anonymous” to other users.
Internal teams (Safety Admins) may associate messages with accounts in rare safety/emergency contexts.

11. Performance Targets (MVP)
Concurrency
Target ~200 concurrent users per room on a single node.
Throughput
Typical message rate: \< 5 messages/second per room.
Latency
Goal: \< 1 second end-to-end delivery under normal conditions.
Availability
Best-effort; no formal SLA.
System should:
Handle node restarts with client reconnects.
Maintain correct day-boundary behavior.

12. Rollout & Extensibility
Feature flags
Control availability via feature flags:
Enable Patient Room first.
Enable Family/Partner Room later.
Ability to disable either room quickly if issues appear.
Extensibility
room_type is a simple enum that can support future additions:
Clinician-led groups.
Topic rooms.
Pseudonym generation and moderation logic is room_type-aware but reusable.

13. Future Improvements (Not in MVP Scope)
These are explicitly out of scope for MVP, but the design should not preclude them:
Distributed and cross-node rate limiting.
Multi-node WebSocket fan-out with pub/sub.
Longer retention and legal-hold support for safety-flagged messages.
Stronger Safety Admin hardening (MFA, IP restrictions, dual-control).
Tamper-evident audit logging (e.g., write-once storage, cryptographic hashing).
Rich message reporting tools and workflows.
Advanced ML-based moderation and crisis detection.
Enterprise compliance features (tenant-specific retention, regional data residency).