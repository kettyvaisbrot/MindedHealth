# Chat Moderation & Crisis Safety Flagging — Technical Planning

Status: **Planned, not yet implemented.** This document supersedes the moderation/safety
sections (§6, §7, §9.3) of [`feature_family_user_chat.md`](feature_family_user_chat.md) — those
sections were written before persistence/retention/encryption existed and before the
Safety Admin approach was reconsidered. This document is the current source of truth
for moderation and crisis handling.

Related: [`feature_family_user_chat.md`](feature_family_user_chat.md) (original chat spec,
persistence/retention/encryption from it is already implemented and live),
[`feature_family_user_chat_tasks.md`](feature_family_user_chat_tasks.md) (original task
breakdown, MuteBan/PII items here replace the equivalent items there).

---

## 1. Executive Goal

Replace the current non-functional placeholder profanity filter
(`PROFANITY_LIST = ["badword1", "badword2"]` in `MindedHealth/consumers.py`) with three
real, independently-shippable protections for the anonymous peer chat (`patient` and
`family` rooms):

1. Blocking harassment/profanity directed at other users.
2. Blocking personally-identifying information (PII) from being posted into an
   anonymous space.
3. Detecting messages that indicate a self-harm/suicide crisis, and responding with a
   real-time resource message plus (where a real, already-assigned clinician exists)
   a live alert to that clinician — replacing the "human Safety Admin reviews a queue"
   model from the original spec, which had no real admin role or on-call process behind
   it.

## 2. Business Objective

MindedHealth serves people managing mental illness (per the developer: "מתמודדי נפש",
including conditions like schizophrenia), not a general wellness audience. The chat is
anonymous peer-to-peer, so there is currently no mechanism at all to catch a message
indicating imminent self-harm — only a stub list that was never filled in. This is a
patient-safety gap, not a nice-to-have, in a product with real users and licensed
therapists already using the platform.

## 3. Planning Scope

### In scope (this document, full engineering detail)
- Phase 1: keyword/regex-based harassment/profanity moderation.
- Phase 2: regex-based PII detection (ID number, email, phone only).
- Phase 3: OpenAI Moderation–based crisis/self-harm detection, with local keyword
  fallback and async re-check on outage.
- MuteBan (chat-only, automatic, 3 violations / 24h → 24h mute).
- ModerationLog (metadata-only audit trail for Phase 1/2 blocks).
- SafetyFlag (encrypted content copy, 30-day retention, exempt from the nightly
  `end_chat_day` wipe).
- Real-time crisis resource message to the sender.
- Real-time clinician alert for `patient`-room crisis messages only.

### Out of scope (explicitly deferred by the developer)
- Full-platform account bans (MuteBan is chat-only).
- Full name / home address detection in PII (no reliable regex pattern exists; would
  require NER, not attempted here).
- A human "Safety Admin" role, dashboard, or review queue — deliberately replaced by
  the automated dual-response design in §7 below.
- `AuditLog` model from the original spec — see §4, Decision 10.
- Fine-tuned BERT-based crisis classifier — see §4, Decision 15 (documented as future
  direction only).
- Automated outbound calls/SMS to real emergency services (police/ambulance) — see §4,
  Decision 3, this was explicitly considered and rejected.

### Mandatory
Phases 1 and 2 (profanity + PII), MuteBan, ModerationLog. These have no external
dependency and are the immediate implementation target.

### Optional / later
Phase 3 (crisis detection) is explicitly scheduled by the developer as a later,
separate implementation pass — it is fully designed here so no further architecture
questions are needed when that pass starts, but it does not ship with Phases 1–2.

---

## 4. Engineering Decisions

| # | Decision | Selected option | Reason | Source |
|---|---|---|---|---|
| 1 | Blocked-message behavior (profanity/PII) | Message is not persisted, not broadcast. Sender receives a clear `message_blocked` error. | Silent drop would leave the sender thinking the message sent. | Developer decision |
| 2 | Crisis-message behavior | Message is not persisted, not broadcast. Sender receives a private resource message instead. | Delivering self-harm content to peers isn't useful; a direct resource response is. | Developer decision |
| 3 | "Real action toward an external party" | Deliberately **not** automated outbound calls/SMS to emergency services (100/101/1221). Real-time clinician alert (for `patient` room, where a `PatientProfile.therapist` exists) is the real action instead. | No public API exists for an app to trigger real dispatch; false positives would send real emergency responders to a stranger's door, with legal/liability exposure. A message to the patient's own already-responsible, licensed therapist is a defensible real escalation instead. | Developer decision, after explanation of the legal/technical infeasibility |
| 4 | `family`-room crisis handling | Resource message to sender only, no clinician alert. | Family members have no assigned therapist in the data model (`FamilyMemberProfile` links to a patient, not a clinician). | Developer decision |
| 5 | Detection mechanism, Phase 1–2 | Regex/keyword, no external AI. | Deterministic, instant, free, no dependency. Appropriate for profanity and structured PII (ID/email/phone). | Developer decision |
| 6 | Detection mechanism, Phase 3 | OpenAI Moderation API (not a general chat-completion prompt) + local keyword fallback. | Moderation API is purpose-built, returns self-harm + harassment/violence categories from a single call, cheaper/faster than a general completion prompt. | Developer decision, after explanation of regex vs LLM vs fine-tuned-BERT tradeoffs |
| 7 | Fine-tuned BERT classifier | Not built now. Documented as a Phase 4 future direction, revisited once Phase 1–3 have produced real labeled data. | Requires a labeled crisis/non-crisis dataset (doesn't exist), ML training infra (doesn't exist in this project), and ideally clinical input on labeling — a multi-week separate project, not a v1 decision. | Developer decision |
| 8 | Implementation order | Phase 1 (profanity) → Phase 2 (PII: ID/email/phone only, name/address waived) → Phase 3 (crisis, later, separate pass). | Ship the dependency-free protections first; crisis detection is bigger in scope and deliberately scheduled later. | Developer decision |
| 9 | PII scope | ID number, email, phone only. Full name and home address explicitly waived for this phase. | No reliable regex pattern for free-text names/addresses; would need NER, out of scope. | Developer decision |
| 10 | `AuditLog` (from original spec) | Not built. | The original spec's `AuditLog` existed to audit a human Safety Admin's de-anonymization actions. That role no longer exists in this design — the real user is already known server-side, and for `patient`-room crises the already-responsible therapist is notified directly, with no separate "unmasking" step to audit. `SafetyFlag` itself is the record of what was detected and when. | Developer decision (implied by dropping the Safety Admin role) |
| 11 | `SafetyFlag` content storage | Own encrypted copy of the message content (`EncryptedTextField`, same pattern as `ChatMessage.content`), not a foreign key to `ChatMessage`. | `ChatMessage` rows are deleted nightly by `end_chat_day`; a FK would leave `SafetyFlag` pointing at deleted content, defeating the purpose of retaining it for clinical review. | Assumption, flagged and confirmed by developer |
| 12 | `SafetyFlag` retention | 30 days, exempt from `end_chat_day`. Deleted by a separate, new scheduled task. | Enough time for clinical review without indefinite retention of sensitive content. | Developer decision |
| 13 | MuteBan trigger | 3 `ModerationLog` violations (profanity or PII, combined) within a rolling 24 hours. | Developer decision | Developer decision |
| 14 | MuteBan duration & scope | 24 hours, auto-expiring; chat-only (blocks `ChatConsumer.connect()`, not the rest of the app). | Full-account suspension is a much heavier, clinically-sensitive action that shouldn't be triggered automatically by a chat filter. | Developer decision |
| 15 | `ModerationLog` content | Metadata only: user, room, category, timestamp. No message content stored. | Minimizes sensitive-data surface while still supporting the MuteBan counter and basic appeal/tuning visibility. | Developer decision |
| 16 | Crisis resource message wording | See §4a below — fixed, developer-approved text with real Israeli crisis-line numbers. | Real emergency/crisis numbers must not be invented by the assistant; developer supplied and approved the source list and final wording. | Developer decision |
| 17 | Phase 3 external-dependency failure mode | Fail-open in real time (message sends normally) + local keyword fallback checked first + async re-check task retried against OpenAI after the fact; if the re-check later flags a crisis, the clinician alert still fires (the message itself can no longer be unsent). | Blocking the entire chat feature on a third-party outage is worse than an occasional missed real-time check; the async re-check preserves the clinician-alert safety net without that tradeoff. | Developer decision |
| 18 | Where the OpenAI Moderation call lives | New `POST /moderate` endpoint on `ai_microservice` (not a direct OpenAI call from Django/`chat/`). | `ai_microservice` already centralizes all OpenAI calls and already has retry/circuit-breaker logic — exactly the resilience behavior Decision 17 needs. Reusing it avoids duplicating OpenAI client/key management inside the Django monolith. | Assumption — matches existing service topology, recommended for developer confirmation before Phase 3 implementation begins |

### 4a. Crisis resource message (final wording, developer-approved)

Sent as a private `crisis_response` WebSocket message to the sender only — never broadcast
to the room.

```
אנחנו רואים שאולי את/ה עובר/ת עלייך רגע קשה. את/ה לא לבד/ה.

אם את/ה בסכנה מיידית — התקשר/י 101.

אפשר גם לפנות אל:
• ער"ן – 1201 (תמיכה נפשית, אנונימי, 24/7)
• אנו"ש – 074-7556155
• סה"ר (סיוע והקשבה ברשת) – 055-9571399
```

This exact text is a config value (`CRISIS_RESOURCE_MESSAGE` in `chat/services.py` or
Django settings), not hardcoded inline in the consumer, so it can be updated without a
code review of consumer logic if a phone number changes.

---

## 5. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Profanity/PII detection | Python `re` (stdlib) | No new dependency |
| Crisis detection (Phase 3) | OpenAI Moderation API, called from `ai_microservice` | `openai` SDK already a dependency of both `requirements-django.txt` and `ai_microservice/requirements.txt` |
| Async re-check (Phase 3) | Celery (`chat/tasks.py`, existing `MindedHealth/celery.py` bootstrap) | Reuses the Celery infra already built for `end_chat_day` |
| Encryption | Existing `chat/fields.py` `EncryptedTextField` / `chat/encryption.py` | Reused as-is for `SafetyFlag.content` |
| Clinician alert delivery | Django email backend (existing `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`) + a new in-app notification (simple model + dashboard banner, or reuse an existing notifications mechanism if one exists — **to confirm during implementation**, not yet checked against the codebase) | |

---

## 6. High-Level Architecture

```
ChatConsumer.receive()
  │
  ├─ 1. rate limit (existing, unchanged)
  ├─ 2. MuteBan check (new) ──── muted? → close(4002) / drop message
  ├─ 3. escape + truncate (existing, unchanged)
  ├─ 4. Phase 1: profanity/harassment regex ── match? → ModerationLog(profanity) + message_blocked + maybe MuteBan
  ├─ 5. Phase 2: PII regex (ID/email/phone) ── match? → ModerationLog(pii) + message_blocked + maybe MuteBan
  ├─ 6. [Phase 3, later] crisis check:
  │      a. local keyword fallback list (fast, always runs)
  │      b. async call to ai_microservice POST /moderate (OpenAI Moderation)
  │      c. on crisis match (either a or b): SafetyFlag(content=encrypted) +
  │         crisis_response to sender + clinician alert (patient room only)
  │      d. on OpenAI failure: message proceeds (fail-open), Celery task
  │         queued to re-check later; late positive still fires the
  │         clinician alert
  └─ 7. none matched → ChatMessage.objects.create() + broadcast (existing, unchanged)
```

`ai_microservice` gains one new endpoint, following the existing `/generate-insight`
pattern (internal-key auth via `X-Internal-Key`, reusing `INTERNAL_API_KEY` and the
existing failure-count/circuit-breaker mechanism):

```
POST /moderate
Headers: X-Internal-Key: <INTERNAL_API_KEY>
Body: {"text": "<message content>"}
Response: {"flagged": true, "categories": {"self-harm": true, "harassment": false, ...}}
```

---

## 7. Database Design

### `chat.ModerationLog` (new)

| Field | Type | Notes |
|---|---|---|
| `id` | PK | |
| `user` | FK → `AUTH_USER_MODEL`, `on_delete=SET_NULL`, `null=True` | |
| `room_name` | `CharField(max_length=100)` | |
| `category` | `CharField`, choices: `"profanity"`, `"pii"` | |
| `created_at` | `DateTimeField(auto_now_add=True)` | |

Index: `(user, created_at)` — powers the MuteBan 24h/3-violation lookup.
No content field (Decision 15).

### `chat.SafetyFlag` (new)

| Field | Type | Notes |
|---|---|---|
| `id` | PK | |
| `user` | FK → `AUTH_USER_MODEL`, `on_delete=SET_NULL`, `null=True` | Real user directly — no pseudonym-only storage, no de-anonymization step (Decision 10) |
| `room_name` | `CharField(max_length=100)` | |
| `chat_day` | `DateField` | For consistency with other chat models |
| `content` | `EncryptedTextField` | Own encrypted copy (Decision 11), not a FK to `ChatMessage` |
| `reason` | `CharField`, e.g. `"self_harm"` | Extensible for future categories |
| `therapist_notified` | `BooleanField(default=False)` | Only meaningful for `patient` room |
| `created_at` | `DateTimeField(auto_now_add=True)` | |

Not touched by `end_chat_day`. Deleted by a new `chat/tasks.py` task,
`purge_old_safety_flags`, scheduled daily, deleting rows where
`created_at < now - 30 days` (Decision 12).

### `chat.MuteBan` (new)

| Field | Type | Notes |
|---|---|---|
| `user` | `OneToOneField` → `AUTH_USER_MODEL` | One row per user who has ever been muted |
| `muted_until` | `DateTimeField(null=True, blank=True)` | If null or in the past, user is not muted — self-expiring, no cleanup task needed |
| `updated_at` | `DateTimeField(auto_now=True)` | |

---

## 8. API Contracts

### WebSocket close codes (extends the existing 4000/4001/4003 convention)

| Code | Meaning | Existing? |
|---|---|---|
| 4000 | Chat day ended | Existing |
| 4001 | Unauthorized | Existing |
| 4003 | Room/role mismatch | Existing |
| **4002** | **Muted** (new) | New — used both when `connect()` is rejected due to an active mute, and when the 3rd violation triggers a mute mid-session |

### New server → client WebSocket message types

```jsonc
// Phase 1/2 block
{"type": "message_blocked", "reason": "moderation"}   // or "reason": "pii"

// Phase 3 crisis (private to sender only, never broadcast)
{"type": "crisis_response", "message": "<CRISIS_RESOURCE_MESSAGE text>"}

// Sent alongside a 4002 close, so the client can show *why* before redirecting
{"type": "muted", "muted_until": "<ISO 8601 timestamp>"}
```

`templates/chat/room.html` needs a new `onclose` branch for code `4002` (distinct from
the existing `4000` → redirect-to-home branch): show the `muted_until` time to the user
before redirecting, rather than silently redirecting like the day-boundary case.

---

## 9. External Integrations

**OpenAI Moderation API**, called from `ai_microservice` (Decision 18), not directly
from Django. Reuses the existing `OPENAI_API_KEY` secret already provisioned via AWS
Secrets Manager, and the existing `X-Internal-Key` auth pattern between Django and
`ai_microservice`.

---

## 10. Infrastructure

No new secrets required for Phase 1–2 (pure regex, no external calls).

Phase 3 requires no *new* secret either — `OPENAI_API_KEY` already exists in Secrets
Manager and is already wired into `ai_microservice` via `bootstrap-env.sh`. The clinician
email alert reuses the existing `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` secrets.

---

## 11. Deployment Strategy

Phases ship independently, each behind its own PR, matching the branch-per-change /
PR-review workflow already used for this project:

1. **Phase 1 (profanity)** — small, self-contained, no migration risk beyond one new
   model. Ships first.
2. **Phase 2 (PII)** — small follow-up PR, same pattern.
3. **MuteBan + ModerationLog** — ships alongside Phase 1 (they're required for Phase 1
   to be meaningful — a violation with no counter has no consequence).
4. **Phase 3 (crisis detection)** — separate, later implementation pass, per the
   developer's explicit sequencing. Requires the new `ai_microservice` endpoint to be
   deployed first.

---

## 12. Execution Strategy

Mandatory work (Phase 1, Phase 2, MuteBan, ModerationLog) has no external dependency
and can be fully implemented, tested, and deployed now. Phase 3 is fully designed in
this document so that when the developer starts that pass, no further architecture
questions are needed — but it is not part of the current execution order.

## 13. Execution Order

1. **Goal:** Replace the placeholder profanity filter with a real one.
   **Deliverable:** `chat/moderation.py` (or similar) with a Hebrew+English
   keyword/regex list; `ModerationLog` model + migration; `receive()` updated to check
   and block.
   **Dependencies:** None.
   **Definition of Done:** A message containing a listed word is blocked, not
   persisted, not broadcast; sender receives `message_blocked`; a `ModerationLog` row
   is created; existing chat tests still pass; new tests cover block + non-block cases.

2. **Goal:** MuteBan enforcement.
   **Deliverable:** `MuteBan` model + migration; `connect()` checks `muted_until`;
   `receive()` counts `ModerationLog` rows in the trailing 24h and sets `muted_until`
   on the 3rd violation, closing the active connection with code 4002.
   **Dependencies:** Step 1 (needs `ModerationLog` to count from).
   **Definition of Done:** 3rd violation within 24h closes the socket with 4002 and
   blocks reconnection until `muted_until` passes; test covers the exact
   3rd-violation boundary.

3. **Goal:** PII detection.
   **Deliverable:** Regex patterns for Israeli ID (with checksum), email, phone;
   wired into the same `receive()` check chain as Step 1, logging
   `ModerationLog(category="pii")`.
   **Dependencies:** Step 1 (shares the block/log/mute code path).
   **Definition of Done:** ID/email/phone in a message is blocked and logged; a
   message containing a free-text name/address is **not** expected to be caught
   (documented limitation, not a bug).

4. **Goal:** Client-side UX for blocks and mutes.
   **Deliverable:** `templates/chat/room.html` handles `message_blocked` (inline error
   near the input) and the new 4002 close code (show `muted_until`, then redirect).
   **Dependencies:** Steps 1–3.
   **Definition of Done:** Manually verified in a browser: a blocked message shows an
   error and the input isn't cleared; a mute shows the unmute time before redirecting.

5. **[Later, separate pass] Goal:** Crisis detection.
   **Deliverable:** `POST /moderate` on `ai_microservice`; `SafetyFlag` model +
   migration + `purge_old_safety_flags` Celery task; crisis check wired into
   `receive()` per §6; clinician alert delivery (email + in-app, patient room only);
   `CRISIS_RESOURCE_MESSAGE` config value; local fallback keyword list; async re-check
   task on OpenAI failure.
   **Dependencies:** Steps 1–4 (shares the block/log code path and client UX
   patterns).
   **Definition of Done:** A crisis-worded test message in the `patient` room is
   blocked, sender receives the exact resource text privately, a `SafetyFlag` row with
   encrypted content is created, and the assigned therapist receives an alert. Same
   message in the `family` room is blocked and resourced, but creates no clinician
   alert. Simulated `ai_microservice` outage still fails open and still eventually
   creates the `SafetyFlag` via the async re-check.

---

## 14. Capability Breakdown

- **Moderation** — profanity/harassment blocking (Step 1).
- **PII Protection** — structured PII blocking (Step 3).
- **Abuse Response** — MuteBan (Step 2).
- **Crisis Safety** — detection, resourcing, clinician alerting (Step 5).

## 15. Definition of Done (feature-level)

- Every phase's per-step Definition of Done (§13) is met.
- No regression in existing chat tests (`chat/tests/test_consumer.py`,
  `test_services.py`, `test_tasks.py`, `test_models.py`, `test_history.py`,
  `test_views.py`).
- `docs/features/feature_family_user_chat.md` §6/§7/§9.3 updated to point here rather
  than describing the now-superseded Safety Admin/AuditLog design.

## 16. Timeline

Rough effort, not calendar dates (no deadline given):
- Steps 1–4 (mandatory, in scope now): small, independently shippable — each a
  few hours to one day of focused work, consistent with the size of prior chat PRs
  (button + timezone fix) done this session.
- Step 5 (Phase 3, later pass): materially larger — new `ai_microservice` endpoint,
  new async re-check task, clinician notification delivery, more test surface. Treat
  as its own planning/implementation cycle when the developer schedules it.

## 17. Risks

- **False positives in the Phase 1/2 keyword list** — could block innocuous messages,
  frustrating real users.
- **False negatives in Phase 3 fallback keyword list** — narrower than the OpenAI
  Moderation API by design; a real crisis message could be missed during an OpenAI
  outage if it doesn't match the curated fallback phrasing.
- **Clinician alert delivery failure** — if email delivery silently fails, the one
  real-world action this design takes for `patient`-room crises doesn't reach anyone.
- **`SafetyFlag` is sensitive data** — a second encrypted-content table alongside
  `ChatMessage`, with a longer retention window (30 days vs. daily wipe) — a larger
  attack/exposure surface if the encryption key or DB access is ever compromised.
- **No real emergency-service integration** — by design (Decision 3); worth restating
  as a residual risk, not just a resolved decision: this system cannot help with
  imminent physical danger the way a real dispatch call could.

## 18. Risk Mitigation

- Keyword lists (Phase 1, and the Phase 3 fallback list) should be reviewed
  periodically using `ModerationLog` volume/category data (Decision 15) to catch
  obvious over- or under-triggering.
- Clinician alert should use Django's email backend with delivery logged (not
  fire-and-forget silently) — worth adding a log line on send success/failure so a
  failure is at least visible in application logs, even without a full retry/alerting
  system in this pass.
- `SafetyFlag` encryption reuses the already-provisioned `CHAT_MESSAGE_ENCRYPTION_KEY` /
  AWS Secrets Manager setup — no new key-management surface introduced.
- The crisis resource message explicitly includes "if in immediate danger, call 101"
  as the first line (Decision 16) — directing genuinely acute situations to real
  emergency dispatch via the user's own action, rather than the system attempting it.

## 19. Decision Traceability

See §4 — every decision lists its selected option, reason, and source. All are
`Developer decision` except Decisions 11 and 18, marked `Assumption` and flagged for
explicit developer confirmation before Phase 3 implementation begins (Decision 11 was
already confirmed in the same planning conversation; Decision 18 is recommended but not
yet explicitly confirmed).

## 20. Planning Validation Checklist

- [x] Every requirement from the discovery conversation is covered.
- [x] Mandatory work (Phases 1–2, MuteBan, ModerationLog) precedes optional/later work
  (Phase 3, BERT).
- [x] Every decision has a source (Developer decision or Assumption, none silent).
- [x] No assumption presented as settled fact — Decision 18 explicitly flagged as open.
- [x] Real crisis-line phone numbers were supplied by the developer, not invented.
- [x] Planning is implementation-ready for Steps 1–4; Step 5 is fully designed but
  intentionally not scheduled yet.
