<div dir="rtl">

# תכנון טכני — Therapist Dashboard Redesign

**סטטוס:** מוכן ליישום. עוקב אחרי `docs/features/feature_therapist_dashboard.md` (מסמך האפיון המאושר).

---

## 1. Executive Goal

לבנות מסך מטפל פונקציונלי במקום השלד הריק הקיים: רשימת מטופלים עם אינדיקציה
מהירה על מצבם, ומסך מטופל בודד עם חמש קטגוריות תוכן (סטטיסטיקות, תיעוד יומי,
זיהוי ימי התקפים, מעקב תרופות, התראות) — הכל בהתאם ל-`feature_therapist_dashboard.md`.

## 2. Business Objective

מטפל/ת שאחראי/ת על מספר מטופלים צריכ/ה לדעת מה קורה איתם בלי לחפור בכל מסך
בנפרד. היום אין שום "מבט על" — המסמך הזה סוגר את הפער.

## 3. Planning Scope

### In Scope
- מסך רשימת מטופלים: פעילות אחרונה, סימון התראה (UI בלבד), ביטול שיוך.
- מסך מטופל: 5 קטגוריות (סטטיסטיקות/תיעוד/התקפים/תרופות/התראות).
- App חדש: `therapist_portal`.
- מודל חדש: `PatientAlert` (ריק/placeholder).

### Out of Scope
- תובנות AI למטפל (סבב אפיון עתידי נפרד).
- ניקוי חוב טכני של שם ה-URL הכפול `therapist_dashboard`.
- עיצוב ויזואלי/CSS.
- מנגנון זיהוי המשבר עצמו (Step 5 במודרציה) — `PatientAlert` הוא רק placeholder.

### Mandatory
כל מה שב-In Scope, לפי סדר העדיפויות שבסעיף 13.

### Optional
אין — כל מה שבתכנון הזה סוכם כנדרש.

---

## 4. Engineering Decisions

| # | Decision | Selected option | Reason | Source |
|---|---|---|---|---|
| 1 | UI approach | Django templates רגילים (server-rendered), GET + query params | כל התחום הזה כבר server-rendered; כל המסכים המבוקשים הם "בחר פילטר → ראה רשימה", לא דורשים אינטראקטיביות בלי רענון | Developer decision |
| 2 | מיקום קוד | App חדש: `therapist_portal` | עקבי עם הדפוס הקיים בפרויקט (`dashboard`, `my_statistics`, `medications`, `insights` — כל תחום ב-app נפרד) | Developer decision |
| 3 | היקף ה-app החדש | רק ה-views/routes **החדשים** (תיעוד/התקפים/תרופות/התראות/ביטול שיוך) עוברים ל-`therapist_portal`. `therapist_dashboard` ו-`patient_detail` הקיימים **נשארים** ב-`users` app בלי שינוי | מזעור סיכון — לא לגעת בקוד קיים/נבדק כדי לפתור בעיה שלא ביקשו לפתור (שם ה-URL הכפול מוגדר Out of Scope) | Assumption (מבוסס על ההעדפה העקבית ב-session הזה למינימום שינוי) — **לאשר** |
| 4 | Routing למסלולים חדשים | Prefix חדש `/therapist-portal/`, עם namespace `therapist_portal` | נמנע במכוון מ-`/therapist/` (כבר תפוס ע"י ה-view היתום `therapist_page`) — לא להוסיף עוד בלבול לאותו path | Developer decision + Existing System (המנעות מהתנגשות קיימת) |
| 5 | ניווט בין חודשים (מסך התקפים) | Query params: `?year=YYYY&month=MM` | פשוט יותר — מסלול אחד, ברירת מחדל טבעית ("בלי פרמטרים = חודש נוכחי") | Developer decision |
| 6 | תאריך במסך "תיעוד" | Query param: `?date=YYYY-MM-DD`, ברירת מחדל = היום | עקביות עם החלטה #5 (query params לפילטור בתוך הפיצ'ר הזה) | Developer decision |
| 7 | חישוב "פעילות אחרונה" | שאילתה חיה: `MAX(date)` על כל 6 מודלי הלוג בכל טעינת עמוד, לא שדה שמור | בקנה מידה הנוכחי (מעט משתמשים) העלות זניחה; שדה שמור דורש signals על 6 מודלים + מיגרציה + סיכון אי-סנכרון | Developer decision (עם המלצה מפורשת בהתחשב בקנה המידה) |
| 8 | שליפת "תיעוד לפי תאריך" | 6 שאילתות נפרדות (אחת לכל מודל), כל אחת מסוננת `user=patient, date=chosen_date`, דרך פונקציית עזר אחת | 6 הטבלאות בלתי-תלויות זו בזו — לא ניתן לאחד לשאילתה אחת בלי לשנות מודלים קיימים (מחוץ לסקופ). כל שאילתה זולה כי מסוננת כבר ליום בודד | Developer decision + Existing System (מבנה המודלים) |
| 9 | ביטול שיוך מטופל | POST endpoint + אישור בצד לקוח דרך `confirm()` פשוט ב-JS, בלי מסך אישור נפרד | תואם לגישת ה-UI (#1) בלי להוסיף עוד route; מספיק להגנה מפני לחיצה בטעות | Developer decision |
| 10 | מודל `PatientAlert` | חדש, שדות: `user` (FK), `room_name`, `reason`, `therapist_notified`, `created_at` — ללא שדה תוכן | מראה-מקום מכוון ל-`SafetyFlag` העתידי (ראו `feature_chat_moderation_safety.md` §7) בלי תשתית הצפנה שלא רלוונטית כאן | Developer decision |
| 11 | חישוב עמידה בתרופות | `expected = medication.times_per_day × ימים בתקופה`; `taken = COUNT(MedicationIntakeLog WHERE time_taken IS NOT NULL)` בטווח; `adherence % = taken/expected` | פשוט, עקבי, לא תלוי בפירוק `dose_times` המדויק | Developer decision |
| 12 | טווח זמן לעמידה בתרופות | נבחר ע"י המטפל/ת: 7 / 30 / 90 ימים, ברירת מחדל 30 | גמישות בלי מורכבות יתר | Developer decision |
| 13 | אימות הרשאה בכל view חדש | זהה בדיוק לדפוס הקיים ב-`patient_detail` (`login_required` + `request.user.therapistprofile` + `patient.therapist == therapist_profile`), מרוכז בפונקציית עזר אחת כדי לא לשכפל 5 פעמים | מונע כפילות קוד (כמו הריפקטור ב-`consumers.py` בשלב 3 של המודרציה); שומר על אותה גבולת אבטחה שכבר נבדקה (IDOR fix) | Assumption (הרחבה ישירה של דפוס קיים) — **לאשר** |
| 14 | דפוס טסטים | `django.test.TestCase` + `self.client.force_login()` + `reverse()`, כמו `users/tests/test_models.py` | עקביות עם שאר הטסטים הקיימים לתחום הזה | Developer decision |
| 15 | מצבי ריק (empty states) | הודעת טקסט פשוטה בעברית לכל מסך ("אין תיעוד ליום זה" / "לא היו התקפים מתועדים בחודש זה" / "לא רשומות תרופות" / "אין התראות") | תוכן UI בלבד, לא משפיע על ארכיטקטורה | Assumption — **לאשר** |

---

## 5. Technology Stack

אין תוספת טכנולוגית — Django 5.1 + DRF הקיימים, ללא ספריות חדשות, ללא JS
חדש (מלבד `confirm()` וניל JS אחד למסך הביטול-שיוך).

---

## 6. High-Level Architecture

```
therapist_dashboard (users app, existing, unchanged)
  └─ patient_detail (users app, existing, unchanged)
       ├─ "Statistics" → my_statistics (existing, unchanged)
       ├─ "Documentation" → therapist_portal:patient_documentation
       ├─ "Seizure days" → therapist_portal:patient_seizures
       ├─ "Medications" → therapist_portal:patient_medications
       └─ "Alerts" → therapist_portal:patient_alerts

therapist_dashboard (list) also gets, per row:
  - last-activity (live query helper, called from users.views.therapist_dashboard)
  - alert indicator (queries PatientAlert.objects.filter(user=patient, resolved=False).exists())
  - "unassign" POST → therapist_portal:unassign_patient
```

כל ה-views החדשים חיים ב-`therapist_portal/views.py`, כל אחד עובר דרך אותה
פונקציית אימות הרשאה (`get_owned_patient_or_404(request, patient_id)`).

---

## 7. Database Design

### `therapist_portal.PatientAlert` (חדש)

| Field | Type | Notes |
|---|---|---|
| `id` | PK | |
| `user` | `ForeignKey(AUTH_USER_MODEL, on_delete=SET_NULL, null=True)` | המטופל/ת שההתראה עליו/ה |
| `room_name` | `CharField(max_length=100)` | מראה-מקום ל-`SafetyFlag.room_name` |
| `reason` | `CharField(max_length=50)` | מראה-מקום ל-`SafetyFlag.reason` |
| `therapist_notified` | `BooleanField(default=False)` | |
| `resolved` | `BooleanField(default=False)` | קובע אם הסימון האדום ברשימה יופיע |
| `created_at` | `DateTimeField(auto_now_add=True)` | |

אין שינוי לאף מודל קיים (`SeizureLog`, `Medication`, `MedicationIntakeLog` וכו').

**הערה לעתיד (Step 5 במודרציה):** כשמנגנון הזיהוי ייבנה, הוא צריך להחליט אם
לכתוב ישירות ל-`PatientAlert` הזה, או ליצור `SafetyFlag` נפרד ולסנכרן ביניהם —
זו החלטה של אותו תכנון עתידי, לא כאן.

---

## 8. API Contracts

כל ה-routes תחת `therapist_portal`, prefix `/therapist-portal/`, namespace `therapist_portal`:

| Route | Method | Params | תיאור |
|---|---|---|---|
| `patient/<int:patient_id>/documentation/` | GET | `?date=YYYY-MM-DD` (ברירת מחדל: היום) | תיעוד יומי מאוחד |
| `patient/<int:patient_id>/seizures/` | GET | `?year=YYYY&month=MM` (ברירת מחדל: חודש נוכחי) | רשימת ימי התקפים |
| `patient/<int:patient_id>/medications/` | GET | `?period=7\|30\|90` (ברירת מחדל: 30) | רשימת תרופות + עמידה |
| `patient/<int:patient_id>/alerts/` | GET | — | רשימת `PatientAlert` (תמיד ריקה כרגע) |
| `patient/<int:patient_id>/unassign/` | POST | — | מנתק `PatientProfile.therapist`, מפנה חזרה ל-`therapist_dashboard` |

כל route מאמת: `login_required` + `request.user.therapistprofile` קיים +
`patient.therapist == therapist_profile` (אותו דפוס בדיוק כמו `patient_detail`
היום ב-`users/views.py`), אחרת → `redirect('home')`.

---

## 9. External Integrations

אין. הכל פנימי (DB + templates).

---

## 10. Infrastructure

אין תוספת — לא נדרש סוד/secret חדש, לא נדרש שינוי ב-`docker-compose.yml`
או ב-`bootstrap-env.sh`.

---

## 11. Deployment Strategy

נכנס דרך `deploy.yml` הקיים (push ל-`main` → build+push image → migrate
אוטומטי → `docker-compose up -d`) — אין צורך בשום שינוי לתהליך הדיפלוי עצמו
(השלב האוטומטי שהוספנו מוקדם יותר ב-session הזה כבר מכסה את ה-migration
של `PatientAlert`).

---

## 12. Execution Strategy

Priority 1 (רשימה) עצמאי לגמרי מ-Priority 2/3 מבחינת קוד, אבל הגיוני לבנות
לפי הסדר כי Priority 1 הוא הבסיס הניווטי לכל השאר.

---

## 13. Execution Order

1. **Goal:** תשתית — יצירת `therapist_portal` app.
   **Deliverable:** `startapp therapist_portal`, רישום ב-`INSTALLED_APPS`,
   `PatientAlert` model + migration, `urls.py` עם ה-namespace, חיווט ב-
   `MindedHealth/urls.py` (`/therapist-portal/`), פונקציית עזר
   `get_owned_patient_or_404`.
   **Dependencies:** אין.
   **Definition of Done:** ה-app קיים, ה-migration רץ, אין עדיין views בפועל.

2. **Goal:** מסך רשימת מטופלים משודרג (Priority 1).
   **Deliverable:** `therapist_dashboard` (ב-`users/views.py`, נשאר במקומו)
   מתעדכן: לכל מטופל/ת בלולאה — פעילות אחרונה (שאילתה חיה), בדיקת
   `PatientAlert` פעיל, כפתור ביטול שיוך (`therapist_portal:unassign_patient`
   + JS confirm). `templates/users/therapist_dashboard.html` מתעדכן בהתאם.
   **Dependencies:** שלב 1 (`PatientAlert`, `unassign_patient` route).
   **Definition of Done:** רשימת מטופלים מציגה פעילות אחרונה נכונה; ביטול
   שיוך עובד ומוגן ב-confirm; סימון אדום קיים ב-UI (תמיד כבוי בפועל).

3. **Goal:** תיעוד לפי תאריך + לינק סטטיסטיקות (Priority 2).
   **Deliverable:** `therapist_portal:patient_documentation` view + template
   חדשים; `patient_detail.html` מקבל שני כפתורים חדשים ("סטטיסטיקות" כבר
   קיים, רק מוודאים שנשאר; "תיעוד" חדש).
   **Dependencies:** שלב 1.
   **Definition of Done:** בחירת תאריך מציגה את כל 6 סוגי הלוג של אותו יום;
   מצב ריק מוצג נכון כשאין תיעוד.

4. **Goal:** זיהוי ימי התקפים, תרופות, התראות (Priority 3).
   **Deliverable:** שלושה views+templates נוספים תחת `therapist_portal`;
   שלושה כפתורים נוספים ב-`patient_detail.html`.
   **Dependencies:** שלבים 1-3 (חולקים את אותו דפוס אימות הרשאה ומבנה URL).
   **Definition of Done:** ניווט חודשים בהתקפים עובד; חישוב עמידה בתרופות
   נכון לפי הנוסחה בהחלטה #11; מסך התראות מציג "אין התראות" (תמיד, כרגע).

5. **Goal:** טסטים.
   **Deliverable:** `therapist_portal/tests/` — טסטי הרשאה (מטפל/ת לא-משויכ/ת
   נדחה, בדיוק כמו `test_patient_detail_authz.py`) לכל route חדש, טסטי
   empty-state, טסט לחישוב עמידה בתרופות, טסט לביטול שיוך.
   **Dependencies:** שלבים 2-4.
   **Definition of Done:** כל הטסטים עוברים; שום regression בטסטים קיימים
   של `users`.

---

## 14. Capability Breakdown

- **Patient List Enhancements** — פעילות אחרונה, סימון התראה, ביטול שיוך.
- **Daily Documentation View** — תיעוד מאוחד לפי תאריך.
- **Seizure Tracking View** — זיהוי ימי התקפים לפי חודש.
- **Medication Adherence View** — רשימת תרופות + מגמת עמידה.
- **Alerts Placeholder** — מוכן מבנית, לא פעיל.

## 15. Definition of Done (feature-level)

- כל 5 היכולות מיושמות ועובדות לפי §13.
- אין regression בטסטים הקיימים של `users`, `dashboard`, `medications`.
- `docs/features/feature_therapist_dashboard.md` מתעדכן לסמן שהתכנון הטכני
  הושלם והמימוש בתהליך/הושלם.

## 16. Timeline

הערכה גסה (לא תאריכים):
- שלב 1 (תשתית): קצר, עבודה טכנית פשוטה.
- שלב 2 (רשימה): בינוני — 6 שאילתות × N מטופלים בלולאה, לוודא שלא איטי.
- שלבים 3-4: כל view חדש קטן ועצמאי יחסית, ניתן לשלוח כ-PR נפרד לכל אחד
  (תואם לדפוס branch-per-PR שכבר נהוג בפרויקט).
- שלב 5: תלוי בכמות ה-views שנבנו.

## 17. Risks

- **ביצועים בעתיד:** שאילתת "פעילות אחרונה" החיה (6 שאילתות × N מטופלים)
  זולה כרגע (מעט משתמשים), אבל תהפוך לבעיה אם מטפל/ת יצבור עשרות מטופלים.
  צוין במפורש כ-trade-off מודע (החלטה #7), לא באג.
- **`PatientAlert` עלול להיות "היתום השני"** אם Step 5 (זיהוי משבר) ייבנה
  מאוחר ולא יתואם עם המודל הזה — יוצר שני מסלולי נתונים דומים
  (`PatientAlert` מול `SafetyFlag` עתידי) אם לא ייעשה תיאום מפורש.
- **שכפול לוגיקת אימות הרשאה** בין `users.views.patient_detail` הקיים
  ל-`therapist_portal`'s `get_owned_patient_or_404` — שתי מימושים דומים
  באפליקציות שונות. מקובל כאן (Decision #3), אבל שווה מעקב.

## 18. Risk Mitigation

- לתעד ב-`PatientAlert` את הכוונה המפורשת (כבר נעשה בהערה בסעיף 7) כדי
  שמי שיבנה את Step 5 לא ימציא מנגנון מקביל בלי לדעת שזה קיים.
- אם/כשמספר המטופלים לכל מטפל/ת יגדל משמעותית, לחזור להחלטה #7 ולשקול
  שדה שמור/קאשינג.

## 19. Decision Traceability

ראו §4 — לכל החלטה מקור (Developer decision / Assumption / Existing System).
שלוש החלטות מסומנות "Assumption — לאשר" (#3, #13, #15) — לא דורשות עצירה
נוספת (הן נבעו ישירות מדפוסים שכבר אושרו ב-session הזה), אבל מפורטות
במפורש כדי שלא יוצגו כעובדה סמויה.

## 20. Planning Validation Checklist

- [x] כל דרישה מ-`feature_therapist_dashboard.md` מכוסה.
- [x] סדר הביצוע תואם לעדיפויות שנקבעו באפיון (1 → 2 → 3).
- [x] לכל החלטה מקור מתועד.
- [x] שום הנחה לא מוצגת כעובדה — כל Assumption מסומנת ומוסברת.
- [x] התכנון מוכן ליישום ע"י מפתח/ת או סוכן AI בלי שאלות ארכיטקטורה נוספות.

---

## 21. Progress Log

**עדכון אחרון:** 2026-10-19. רשימת ה-PRs תוכננה מחדש תוך כדי עבודה (ראו תת-סעיף הבא) — זה המקור הכי מעודכן, לא §13 המקורי.

### בוצע

- **PR 1 — תשתית** ([#58](https://github.com/kettyvaisbrot/MindedHealth/pull/58), **ממוזג**): app `therapist_portal`, מודל `PatientAlert`+migration, `urls.py` עם namespace ב-`/therapist-portal/`, helper `get_owned_patient_or_404` ב-`therapist_portal/utils.py`. בדיוק לפי §13 שלב 1.
- **PR 2 — ביטול שיוך + סימון התראה** ([#59](https://github.com/kettyvaisbrot/MindedHealth/pull/59), **ממוזג**): scope צומצם ביחס ל-§13 שלב 2 המקורי — הוצא ממנו נושא "פעילות אחרונה" (עבר ל-PR נפרד, ראו למטה). כולל: `therapist_portal.views.unassign_patient` (POST, מוגן ב-`get_owned_patient_or_404`), חיווט ב-`therapist_portal/urls.py`, `has_alert` annotation ב-`users.views.therapist_dashboard`, כפתור Unassign + סימון 🔴 ב-template, 3 טסטים ב-`therapist_portal/tests.py`.
  - **תגלית אגב (לא תוקנה, רק עוקפה בטסטים):** `MindedHealth/middleware.py::LogoutOnServerStartMiddleware` מוחק את כל ה-sessions בטעינה הראשונה של שרשרת המידלוור — ב-Django test client הטעינה הזו עצלנית (קורית רק בבקשה הראשונה שבאמת נשלחת), אז כל טסט עם `force_login()` מתנתק באמצע אם לא עוקפים את זה. הפתרון הנוכחי: בקשת "חימום" ב-`setUp()` של הטסטים, מקומי לקובץ הטסטים בלבד. **שווה בדיקה נפרדת** — אותו מידלוור גם מתנתק את כל המשתמשים האמיתיים בכל עליית worker בפרודקשן, לא רק בקריסה.
- **PR 3 — פעילות אחרונה** ([#60](https://github.com/kettyvaisbrot/MindedHealth/pull/60), **ממוזג**): `therapist_portal.utils.get_last_activity_by_user` (6 שאילתות סה"כ, ראו החלטה #18 למטה), `days_since_activity` + `needs_attention` ב-`users.views.therapist_dashboard`, תצוגת "לפני X ימים"/"מטופל/ת חדש/ה" + סימון משותף ב-template, 10 טסטים חדשים (סה"כ 13 ב-`therapist_portal/tests.py`).
  - **תגלית אגב נוספת (רחבה יותר ממה שחשבנו ב-PR 2):** באג התאימות ל-Python 3.14 שגילינו ב-PR 2 (ב-`assertRedirects`) מתברר שהוא **לא ספציפי ל-assertRedirects** — כל `self.client.get()` על מסך שמרנדר template קורס באותה צורה תחת `manage.py test` בסביבה הזו (Django מחבר receiver ל-signal `template_rendered` רק בתוך `Client.request()`, וה-receiver הזה הוא שקורס). הפתרון ב-PR 3: טסטי האינטגרציה קוראים ל-view ישירות דרך `RequestFactory` במקום `self.client` — זה עוקף את ה-instrumentation השבור (שמחובר רק ל-`Client`, לא לקריאה ישירה לפונקציה) בלי לוותר על בדיקת ה-HTML האמיתי שמוחזר. **רלוונטי לכל טסט עתידי** שצריך לבדוק תוכן של עמוד מרונדר.
- **PR 4 — תיעוד יומי** ([#61](https://github.com/kettyvaisbrot/MindedHealth/pull/61), **ממוזג**): `therapist_portal.views.patient_documentation` — ה-view *הראשון* האמיתי ב-`therapist_portal` (עד עכשיו היה שם רק `unassign_patient`). שולף את כל 6 מודלי הלוג עבור תאריך נבחר (`?date=`, ברירת מחדל היום), מציג רק קטגוריות שיש בהן תיעוד, "No documentation for this day" רק כש**כולן** ריקות. `therapist_portal/formatters.py` חדש — פונקציית פירמוט נפרדת לכל מודל, כל אחת מחזירה `[(label, value), ...]`, כך שה-template נשאר גנרי (לולאה אחת) למרות ששדות כל מודל שונים לגמרי. שמות תרופות (`Medication.name`) נפתרים בשאילתה אחת מרוכזת (`medication_ref_id` הוא int רגיל, לא FK אמיתי). כפתור "Documentation" חדש ב-`patient_detail.html`. 7 טסטים חדשים (סה"כ 20 ב-`therapist_portal/tests.py`).

### תוכנית PRs מעודכנת (9 PRs — עודכן 2026-10-19, נוסף PR "Patient Overview")

| # | PR | סטטוס |
|---|---|---|
| 1 | תשתית | ✅ ממוזג (#58) |
| 2 | ביטול שיוך + סימון התראה | ✅ ממוזג (#59) |
| 3 | פעילות אחרונה | ✅ ממוזג (#60) |
| 4 | תיעוד יומי | ✅ ממוזג (#61) |
| 5 | ימי התקפים | ⬜ הבא בתור — תכנון ראשוני למטה, עדיין לא נדון/הוכרע סופית. **שינוי:** חישוב ספירת ההתקפים צריך לצאת כפונקציית עזר נפרדת (לא inline בתוך ה-view), כדי ש-PR 7 (Overview) יוכל לעשות לה reuse |
| 6 | עמידה בתרופות | ⬜ לא התחיל. **אותו שינוי:** נוסחת העמידה (החלטה #11 המקורית) צריכה לצאת כפונקציית עזר נפרדת מאותה סיבה |
| **7** | **Patient Overview (חדש)** — ראו פירוט מלא למטה | ⬜ לא התחיל — **תלוי ב-5+6** (צריך את פונקציות העזר שלהם) |
| 8 | התראות (placeholder) | ⬜ לא התחיל |
| 9 | טסטים (כיסוי כולל) | ⬜ לא התחיל — ייתכן שיתכווץ/ייעלם, כי כל PR כבר כולל טסטים משלו (20 קיימים) |

### PR 7 — Patient Overview (חדש, הוגדר 2026-10-19)

**רקע:** יזמה של המשתמשת, בעקבות שאלה "אם היית מתכננת/מעצבת/מפתחת את המוצר — מה היית שמה במסך המטופל?". הבעיה שזוהתה: 5 כפתורי הקטגוריה הנפרדים (Statistics/Documentation/Seizures/Medications/Alerts) דורשים 5 לחיצות כדי להבין "מה מצב המטופל/ת" — ואין דרך לראות קשר בין נתונים משני מסכים שונים (למשל הפסקת תרופות לפני התקף) בלי לפתוח את שניהם ולהשוות ידנית.

**מה זה:** רצועת מידע קצרה בראש `patient_detail.html`, **מעל** חמשת כפתורי הקטגוריה, עם 3 מספרים:
1. פעילות אחרונה (reuse ישיר של `get_last_activity_by_user` מ-PR 3, שום שינוי)
2. עמידה בתרופות ב-30 הימים האחרונים (%)
3. מספר התקפים ב-30 הימים האחרונים

| # | החלטה | הבחירה | נימוק |
|---|---|---|---|
| 27 | חלון זמן לרצועה | קבוע על 30 יום, בלי אפשרות שינוי | הגמישות (7/30/90) שייכת למסך המפורט (PR 6); הרצועה היא glance מהיר בלבד |
| 28 | מקרה קצה — אין בכלל תרופות רשומות | "No medications" ולא "0%" | 0% משתמע שיש מרשם והמטופל/ת לא עומד/ת בו — זה שונה ממצב שאין בכלל תרופות |
| 29 | סימון חזותי נוסף על מספר "מדאיג" | **אין** — מידעי טהור בשלב זה | נמנעים מהרחבת סקופ (עקבי עם "אין AI/תובנות" ב-Out of Scope המקורי) |
| 30 | ארכיטקטורה | חישוב עמידה בתרופות וספירת התקפים חייבים לצאת כפונקציות עזר עצמאיות ב-`therapist_portal/utils.py` (לא קוד inline בתוך views של PR 5/6) | כדי ש-PR 7 יוכל לקרוא לאותה פונקציה בלי לשכפל נוסחה; קובע מגבלה על **איך** PR 5/6 עצמם נבנים, לא רק מה PR 7 עושה |

**תלות:** PR 5 + PR 6 (ולא רק סדר כרונולוגי — תלות קוד אמיתית בפונקציות העזר שלהם).

**עדיין לא הוגדר** (ידונו לפני הבנייה בפועל, כרגיל): מיקום מדויק בעיצוב, מה קורה אם גם אין עמידה וגם אין התקפים בכלל (patient חדש/ה לגמרי).

### PR 4 — החלטות שהתקבלו

| # | החלטה | הבחירה | נימוק |
|---|---|---|---|
| 24 | בחירת תאריך ב-UI | `<input type="date">` (לוח שנה מובנה של הדפדפן), `onchange` שולח את הטופס אוטומטית | נבחר על ידי המשתמשת — גם פותר את נושא "תאריך לא תקין" (הדפדפן תמיד שולח פורמט תקין או כלום) |
| 25 | רמת פירוט בתצוגה | **פירוט מלא, שדה-אחר-שדה** (לא רק `__str__` כללי) — לכל מודל פונקציית פירמוט ייעודית ב-`formatters.py` | נבחר על ידי המשתמשת ("אפשרות B") — רוצה לראות בדיוק מה תועד בכל שדה, לא רק "שמשהו תועד" |
| 26 | מצב ריק | הודעה אחת כללית ("No documentation for this day") **רק** כשכל 6 הקטגוריות ריקות; מספיקה קטגוריה אחת עם תיעוד כדי שהיא תוצג ואחרות הריקות פשוט לא מופיעות (לא מוצגות בנפרד כ"ריקות") | נבחר על ידי המשתמשת |

### PR 3 — החלטות שהתקבלו (עדכון/תוספת ל-§4, לא היו בתכנון המקורי)

| # | החלטה | הבחירה | נימוק |
|---|---|---|---|
| 16 | הגדרת "פעילות אחרונה" | `MAX(date)` על כל 6 מודלי הלוג (`FoodLog`, `SportLog`, `SleepingLog`, `Meetings`, `SeizureLog`, `MedicationIntakeLog`) — **לא** לפי login (`User.last_login`) | נדון במפורש: login הוא סיגנל חלש מדי קלינית (אפשר להתחבר בלי לדווח כלום). המטרה היא לזהות ניתוק מהטיפול, לא שימוש באפליקציה. מספיקה רשומה אחת בכל קטגוריה שהיא כדי "לזכות" אם היא ה-MAX |
| 17 | מקרה קצה — אין אף רשומה | `last_activity = None`, מוצג כ-"Never" ב-UI | לא שגיאה, לא קריסה — מטופל/ת חדש/ה או ללא תיעוד בכלל חייב/ת להיות ניתן לייצוג |
| 18 | אופטימיזציית שאילתות | **6 שאילתות סה"כ** (batched, `values('user_id').annotate(Max('date'))` על כל ה-`user_id`-ים של המטפל/ת בבת אחת לכל מודל) — **לא** 6 שאילתות-לכל-מטופל (שהיו הופכות ל-`6×N`) | נדון במפורש מול הסיכון שכבר תועד ב-§17 המקורי ("תהפוך לבעיה אם מטפל/ת יצבור עשרות מטופלים"). הגרסה החדשה היא O(1) שאילתות ביחס למספר המטופלים במקום O(N), בלי שום פשרה על ההגדרה הקלינית — תוצאה זהה, רק מחושבת ביעילות |
| 19 | מיקום הקוד | פונקציית עזר `get_last_activity_by_user(user_ids)` חדשה ב-`therapist_portal/utils.py` (לצד `get_owned_patient_or_404` מ-PR 1); `users.views.therapist_dashboard` רק קורא לה וממפה לכל `patient.last_activity` | לוגיקה גנרית שסביר שתידרש שוב (למשל במסך תיעוד יומי, PR 4); `therapist_dashboard` עצמו נשאר ב-`users` ללא שינוי מבני (עקבי עם החלטה #3) |

**מגבלה ידועה, לא נפתרת כרגע (הוחלט במפורש להשאיר כ-trade-off מודע):** "פעילות אחרונה" מערבב קטגוריות בעלות משקל קליני שונה — מטופל/ת שמתעד/ת שינה/אוכל כל יום אך לא תרופות/התקפים כבר זמן רב יראה/תראה "פעיל/ה". לא נפתר ב-PR 3 כי המסכים הייעודיים (PR 5 — התקפים, PR 6 — תרופות) כבר נותנים את הדיוק הקטגוריאלי בפירוט מלא. "פעילות אחרונה" ברשימה היא רק שכבת טריאז' ראשונית.

### הוכרע (2026-10-19) — פורמט התצוגה ב-UI

| # | החלטה | הבחירה | נימוק |
|---|---|---|---|
| 20 | פורמט תצוגה | "לפני X ימים" (לא תאריך גולמי) | נבחר על ידי המשתמשת |
| 21 | סף לסימון אדום | **5 ימים** בלי תיעוד | נבחר על ידי המשתמשת |
| 22 | מקרה קצה — אין אף תיעוד (`last_activity=None`) | מוצג כ-**"מטופל/ת חדש/ה"**, בנייטרלי — **לא** מסומן באדום | מטופל/ת חדש/ה שעדיין לא הייתה לו/ה הזדמנות לתעד לא אמור/ה להיראות כמו מצב דחוף |
| 23 | יחס בין סימון חוסר-פעילות לסימון `has_alert` (PatientAlert) | **סימון אחד משותף** — "צריך/ה תשומת לב" (`needs_attention`), מופעל ע"י has_alert **או** חוסר פעילות 5+ ימים | פשוט יותר למטפל/ת, לא דורש להבחין בין שני סוגי אדום. ה-trade-off (לא ניתן לדעת מהסימון בלבד *איזו* מהסיבות הפעילה אותו) התקבל במודע |

### PR 3 — קבצים ומימוש (סופי, מוכן לבנייה)

| קובץ | מה משתנה |
|---|---|
| `therapist_portal/utils.py` | ➕ `get_last_activity_by_user(user_ids)` — 6 שאילתות סה"כ (batched), מחזירה `{user_id: date או None}` |
| `users/views.py` | ✏️ `therapist_dashboard` — קורא ל-`get_last_activity_by_user`, מחשב לכל מטופל/ת `days_since_activity` ו-`needs_attention = has_alert OR (days_since_activity is not None and days_since_activity >= 5)` |
| `templates/users/therapist_dashboard.html` | ✏️ הסימון האדום עובר מ-`has_alert` בלבד ל-`needs_attention`. טקסט: "מטופל/ת חדש/ה" (אין תיעוד) או "לפני X ימים" |
| `therapist_portal/tests.py` | ➕ 10 טסטים — ראו פירוט למטה |

### PR 3 — תוכנית טסטים (10 טסטים)

**רמה 1 — `get_last_activity_by_user` (פונקציית עזר, בלי HTTP):**
1. מטופל/ת עם רשומות במספר מודלים → MAX נכון מביניהם
2. מטופל/ת בלי אף רשומה → `None`
3. כמה מטופלים בבת אחת עם ערכים שונים → בדיקת "זליגה" — כל מטופל/ת מקבל/ת את התאריך **שלו/ה**, לא של מטופל/ת אחר/ת (הסיכון העיקרי בגישת ה-batching)
4. `assertNumQueries(6)` סביב הקריאה, עם מספר user_ids משתנה → מוודא בפועל שזה נשאר O(1) ולא ייסחף בחזרה ל-O(N) בעתיד

**רמה 2 — `therapist_dashboard` (אינטגרציה מלאה):**
5. פעילות מהיום → `needs_attention=False`, טקסט נכון
6. בדיוק 5 ימים (גבול הסף) → **כן** מסומן (`>=`, לא `>`)
7. 4 ימים (יום לפני הסף) → **לא** מסומן
8. אין תיעוד בכלל → "מטופל/ת חדש/ה", **לא** מסומן
9. `PatientAlert` פעיל + פעילות מהיום → מסומן בגלל ההתראה (בודק את ה-`OR`)
10. `PatientAlert` עם `resolved=True` + פעילות מהיום → **לא** מסומן (התראה סגורה לא "תוקעת" סימון)

### נקודת עצירה (עודכן 2026-10-19, סוף היום)

**PR 4 הושלם ומוזג.** כל 20 הטסטים (`therapist_portal`) עוברים, אין regression.

**התוכנית המחודשת (9 PRs, ראו טבלה למעלה)** כוללת PR חדש — **PR 7, "Patient Overview"** — שנוסף היום בעקבות יוזמת המשתמשת. 4 ההחלטות שלו (#27-30) כבר סגורות, כולל המגבלה הארכיטקטונית על PR 5/6 (חייבים לחלץ את החישובים שלהם לפונקציות עזר נפרדות).

**הבא בתור בפועל: PR 5 — ימי התקפים.** שתי נקודות פתוחות עדיין **לא** הוכרעו:
1. איך בדיוק נראה ה-UI לניווט בין חודשים (חיצי קודם/הבא? `<input type="month">`? רשימה?)
2. מה קורה אם מבקשים חודש עתידי (או מוקדם מדי)

**בנוסף, לזכור ב-PR 5 (ו-PR 6 אחריו):** לבנות את לוגיקת החישוב (ספירת התקפים / עמידה בתרופות) כפונקציית עזר עצמאית ב-`therapist_portal/utils.py` מההתחלה, לא inline בתוך ה-view — כדי ש-PR 7 יוכל לעשות reuse נקי בלי שכפול.

**בפעם הבאה:** להתחיל מהכרעת שתי הנקודות הפתוחות של PR 5, בדיוק כמו שעשינו עם PR 3/4, ואז לבנות.

</div>
