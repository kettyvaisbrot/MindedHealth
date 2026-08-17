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

</div>
