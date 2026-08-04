# Test debt: what's skipped in CI and why

This tracks every test currently marked `skip` in CI (`Tests` workflow), why it's
skipped, and what it would take to bring it back. None of these block CD —
`deploy.yml` runs on every push to `main` regardless of skip count, as long as
the `Tests` job itself is green (a skip counts as green, a failure doesn't).

All of these were discovered on 2026-08-04, when the test suite was run in a
clean environment for the first time via GitHub Actions. None are related to
the chat feature or the CI setup itself — they predate both.

---

## 1. Medication logging tests (6 files) — biggest item

**Files:**
- `dashboard/tests/services/test_services_dashboard_service.py`
- `dashboard/tests/services/test_services_medication.py`
- `dashboard/tests/services/test_services_medication_service.py`
- `dashboard/tests/views/test_views_log_medication.py`
- `dashboard/tests/views/test_medication_log_api_view.py`

**What happened:** medication tracking was refactored at some point —
`medications.models.MedicationLog` (a model with a `medication` foreign key)
was replaced by `dashboard.models.MedicationIntakeLog` (which uses a plain
`medication_ref_id` integer instead of a foreign key). These test files still
write against the old shape.

**What it needs:** understand `dashboard/services/medication_service.py` as it
exists today, then rewrite each test's fixtures and assertions against
`MedicationIntakeLog` / `medication_ref_id`. This is not a rename — the data
model changed shape, so the tests need real re-authoring, not search/replace.

---

## 2. Dashboard log view tests (7 files) — second biggest item

**Files:**
- `dashboard/tests/views/test_food_log_api_view.py`
- `dashboard/tests/views/test_views_meetings_log_api.py`
- `dashboard/tests/views/test_views_seizure_log_api.py`
- `dashboard/tests/views/test_views_sleeping_log_api.py`
- `dashboard/tests/views/test_views_sport_log_api.py`
- `dashboard/tests/views/test_views_dashboard_home.py`
- `dashboard/tests/views/test_views_daily_documentation.py`

**What happened:** `dashboard/views.py` was refactored from one view +
serializer per log type (`FoodLogSerializer`, `get_food_logs`,
`delete_food_log`, etc.) into a single generic, config-driven system:
`category_summary_page`, `log_category`, `CategorySummaryView`,
`CategoryEditView`, driven by `dashboard/category_config.py`. The old
per-type functions and serializer names these tests `@patch(...)` no longer
exist anywhere in `dashboard/views.py`.

The URL names changed too — `dashboard/urls.py` now has `dashboard_home`
and `category_summary` (namespaced as `dashboard:...`), not `home` or
`daily_documentation`, which is what two of these files still `reverse()`.

**What it needs:** these aren't broken tests, they're tests of a UI/API shape
that was deliberately replaced. Decide whether the generic category system
needs test coverage at all (it may already be covered elsewhere — worth
checking for `test_category_*` files before writing anything new), and if so,
write fresh tests against `category_summary_page` / `CategorySummaryView` /
`CATEGORY_CONFIG` — not a fix to the old ones.

---

## 3. Dashboard serializer tests (1 file)

**File:** `dashboard/tests/serializers/test_dashboard_serializers.py`

**What happened:** `FoodLogSerializer`, `SportLogSerializer`,
`MeetingsSerializer`, `SeizureLogSerializer`, `SleepingLogSerializer` all
declare `user = serializers.HiddenField(default=serializers.CurrentUserDefault())`.
`CurrentUserDefault()` reads the user off `serializer.context["request"]`.
These tests instantiate the serializers directly without passing a context,
so `CurrentUserDefault()` raises `KeyError: 'request'`.

Separately worth knowing: as of this week these 5 serializers aren't called
from any real view (`dashboard/views.py` no longer references them — see
item 2 above). They may be dead code.

**What it needs:** either (a) pass `context={"request": <a mock or real
request with .user set>}` when constructing each serializer in the tests, or
(b) if item 2's investigation confirms these serializers are genuinely
unused, delete both the serializers and their tests instead of fixing them.

---

## 4. Insights full-flow tests (1 file)

**File:** `insights/tests/test_full_flow.py`

**What happened:** this test exercises the real internal-JWT flow between
Django and insights_service, which needs a real JWT key pair. CI doesn't
have one configured, so it fails with `jwt.exceptions.InvalidKeyError:
Could not parse the provided public key`.

**What it needs:** generate a throwaway JWT key pair (same pattern already
used for `CHAT_MESSAGE_ENCRYPTION_KEY` in `test.yml` — generated fresh each
CI run, never a real secret) and wire it into the relevant env vars in
`.github/workflows/test.yml`. This one is the closest to a pure CI-config
fix, not a code fix — probably the easiest item on this list.

---

## 5. `test_family_dashboard_access` (1 test)

**File:** `users/tests/test_models.py`, class `UsersViewsTest`

**What happened:** the test calls `self.client.force_login(self.family_user)`
and references `self.family_profile`, but `UsersViewsTest.setUp()` never
creates either — it only creates a therapist and a patient. This test may
never have passed.

**What it needs:** add a `FamilyMemberProfile` fixture to `setUp()`, linked
to the existing `patient_profile` (see `users/models.py:FamilyMemberProfile`
for the required fields: `user`, `related_patient`, `relation`).
Small, self-contained fix — good first item to pick up.

---

## Suggested order

Cheapest → most involved: **#5 → #4 → #3 → #1 → #2**. Items 1 and 2 both
require understanding current business logic before touching anything, not
just a mechanical fix — budget real time for those two, not a quick pass.
