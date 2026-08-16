# Therapist Dashboard Redesign — Feature Discovery

Status: **Discovery complete. Technical planning not yet started.** This document
captures the requirements-discovery pass for redesigning the therapist-facing
screens. It is the source of truth to resume from when technical planning begins.

---

## 1. Why this exists

The therapist dashboard today is a functional-but-empty shell: it lists assigned
patients and lets a therapist add one by email, but shows no clinical content at
all. A therapist has to leave the dashboard entirely (via `my_statistics`) to see
anything about a patient. This document defines what the dashboard and the
per-patient screens should actually contain.

This discovery pass was triggered by removing a dead "Family Member" button from
`templates/users/patient_detail.html` (PR #50) — it linked to `family_dashboard`,
a view that only the family member themselves can access
(`if request.user != family_member.user: return redirect('home')`). There was
never a real therapist-facing screen behind that button. Rather than patch it,
the developer asked to rethink the whole therapist experience from scratch.

## 2. Current state (as of this document)

- **`users/views.py` `therapist_dashboard`** (mapped to `/users/therapist-dashboard/`,
  URL name `therapist_dashboard`) — the real, reachable view. Renders
  `templates/users/therapist_dashboard.html`: "Welcome, {username}", a flat list
  of assigned patients (each linking to `patient_detail`), an "add patient by
  email" form (POST, assigns an unclaimed `PatientProfile` to this
  `TherapistProfile`), and a logout button. No styling, no summary, no
  notifications.
- **`templates/users/patient_detail.html`** — patient username heading, a "View
  Statistics" button linking to the separate `my_statistics` app (sleep/sport/
  food/medication/seizure logs live there), and a back-to-dashboard link.
- **Data model** (`users/models.py`): `User(role: patient/therapist/family)`,
  `TherapistProfile(user, specialization, license_number)`,
  `PatientProfile(user, therapist FK)`,
  `FamilyMemberProfile(user, related_patient OneToOne)`.
- **`dashboard` app models** (the actual activity logs, per `CLAUDE.md`):
  `FoodLog`, `SportLog`, `SleepingLog`, `Meetings`, `SeizureLog`
  (`user, date, time, duration_minutes`), `MedicationIntakeLog`
  (`user, medication_ref_id, date, time_taken, dose_index`), `FeltOffLog`.
- **`medications` app**: `Medication(name, times_per_day, dose, user, dose_times)`
  — the prescribed-medication list, separate from the daily intake log above.
- **No notification/alert model exists anywhere in the codebase today.**

### Known tech debt (flagged during discovery, not fixed here)

There are **two URL patterns both named `therapist_dashboard`**:
`MindedHealth/urls.py` → `/therapist/` → an orphaned `therapist_page` view (no
context passed, renders the same template broken/empty) and a separate unused
template `templates/therapist_page.html`; `users/urls.py` → `/users/therapist-dashboard/`
→ the real, working view. Empirically confirmed (`reverse('therapist_dashboard')`)
that the `users/urls.py` one wins, so this isn't an active bug today — but the
orphaned view+template is dead code worth cleaning up eventually, not in scope
for this pass.

## 3. Finalized requirements

### 3.1 Main dashboard screen (patient list) — priority 1

- List of patients assigned to the therapist, each navigable to their detail
  screen.
- **Red indicator** next to any patient with an active alert. **UI-only for
  now** — there is no data source yet (see §3.3, Alerts), so this indicator
  will exist but never actually light up until the crisis-detection engine
  (moderation Step 5, see `feature_chat_moderation_safety.md`) is built.
- **"Last activity"** shown per patient in the list (e.g. "last logged 3 days
  ago") — helps a therapist spot disengaged patients without opening each one.
- Existing "add patient by email" form, kept as-is.
- **New: unassign a patient** (not just add) — a therapist can remove the
  link between themselves and a patient, not only create it.

### 3.2 Patient detail screen — five separate buttons/categories

| Priority | Button | Content |
|---|---|---|
| 2 | **Statistics** | Existing link to `my_statistics`, unchanged. |
| 2 | **Documentation by date** | Therapist picks a past or current date; shows **all logs from that day together** (food, sport, sleep, meetings, medication intake, seizure) — one combined daily view, not split by log type. |
| 3 | **Seizure day identification** | List of dates with seizures, grouped by month, **with navigation to previous months** (not just the current month). Separate button from Statistics — not a section within it. |
| 3 | **Medications taken** | **Not** a single-day view (that's what Documentation is for). Instead: the patient's **current prescribed medication list** (name, dose, times/day) **plus adherence history over a period** (e.g. doses taken vs. scheduled over the last 30 days, per medication) — a trend view, distinct in kind from Documentation's single-day view. |
| 3 | **Alerts** | Shows if/when a message was flagged for self-harm content (date + time). **Empty/placeholder screen for now** — the detection engine itself (moderation Step 5) doesn't exist yet. This screen and the red list-indicator (§3.1) share the same "not wired to real data yet" status. |

### 3.3 Explicitly out of scope / deferred

- **AI-generated insights for therapists** (pattern/trigger identification —
  cross-referencing a patient's logs to surface things like "seizures tend to
  follow poor sleep," not just the existing patient-facing 7-day GPT summary
  in `insights_service`). Developer explicitly asked for this to get its own
  separate discovery pass later — do not fold it into this document or into
  the therapist-dashboard implementation.
- The two-URL-name tech debt (§2) — noted, not addressed here.
- Visual design/CSS — content and functionality take priority; no styling
  requirements were specified in this pass.

## 4. Build order (developer-specified priority)

1. Patient list + navigation to a single patient + unassign + last-activity
   indicator (foundational; everything else hangs off patient detail).
2. Statistics link (trivial, already exists) + Documentation-by-date.
3. Seizure day identification, Medications taken, Alerts placeholder.

## 5. Open dependency to track

The Alerts screen (§3.2) and the list red-indicator (§3.1) are both
**structurally ready but functionally inert** until moderation Step 5 (crisis
detection, see `docs/features/feature_chat_moderation_safety.md` §13 step 5) is
implemented. When that step is eventually built, its `SafetyFlag` model and
therapist-alert delivery mechanism should populate these two surfaces rather
than inventing a new notification path.

## 6. Next step

Technical planning (technologies, DB schema for any new fields/models,
API/view contracts, execution order) has **not** started. Resume with the
`technical-planning` process against this document when the developer is ready.
