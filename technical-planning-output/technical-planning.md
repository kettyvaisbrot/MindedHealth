<!-- dir="rtl" lang="he" -- מסמך זה כתוב בעברית, מיושר מימין לשמאל. מונחים טכניים, שמות קבצים, שמות שדות ומזהי קוד נשארים באנגלית. -->

# תוכנית הטמעה: שמירת הודעות צ'אט עם מחיקה בגבול היום

**פיצ'ר:** Chat Message Persistence with Day-Boundary Retention
**מערכת:** MindedHealth — Django 5.1 + Channels 4.2 + Redis + PostgreSQL/SQLite
**מסמך מקור:** תהליך Feature Discovery + Technical Planning אינטראקטיבי, המשך ל-`docs/features/feature_family_user_chat.md`
**סטטוס:** מוכן לסקירה — טרם יושם

---

## 1. Executive Goal

להפוך את הצ'אט האנונימי הקיים ב-MindedHealth מ**שידור חי בלבד, ללא שמירה** ל**שיחה עם היסטוריה תוך-יומית**, כאשר מדי לילה (23:59 שעון ישראל) כל תוכן היום נמחק לצמיתות ומשתמשים מחוברים מנותקים בעדינות — כך שכל יום מתחיל "נקי" מבחינת תוכן וזהות (כינוי חדש).

## 2. Business Objective

המוצר הוא מערכת בריאות נפשית עם משתמשים אמיתיים ומטפלים מוסמכים. הצ'אט האנונימי קיים כדי לאפשר תמיכה בין-משתמשים (patient-to-patient, family-to-family) מבלי לחשוף זהות. הפיצ'ר הזה:
- הופך שיחה קיימת (רק בזמן אמת) לשימושית בפועל — משתמש שמצטרף מאוחר יכול לראות מה נכתב קודם באותו יום.
- שומר על העיקרון המרכזי של אנונימיות תוך-יומית: אין הצטברות נתונים מעבר ליום בודד, לא בתוכן ולא בזהות.
- מכין תשתית (טבלת הודעות אמיתית) שפריטים עתידיים ברשימת הפיצ'רים המלאה (Safety Flagging, Audit Log) יוכלו להסתמך עליה.

## 3. Planning Scope

### In Scope
- מודל `ChatMessage` חדש, עם הצפנה ברמת השדה על תוכן ההודעה.
- שמירת כל הודעה שנשלחת (בנוסף לשידור הקיים בזמן אמת).
- שליחת היסטוריית הודעות למשתמש עם התחברות, בעימוד (pagination) של 10 הודעות, מהחדש לישן, עם טעינה נוספת בגלילה אוטומטית.
- Job יומי (Celery task, רץ 23:59 Asia/Jerusalem) שמוחק את כל הודעות היום **וגם** את שיוכי הכינויים (`PseudonymAssignment`) של אותו יום, ומנתק בכוח כל מי שמחובר לחדר באותו רגע.
- קוד סגירה ייעודי (4000) לניתוק בגלול יום, מבחין מכל סיבת ניתוק אחרת.
- הקמת תשתית Celery בסיסית מאפס (לא קיימת היום בפרויקט בכלל).
- הצפנת שדה `content` באמצעות עטיפה דקה מעל הספרייה `cryptography` הקיימת בפרויקט.

### Out of Scope (במפורש, לפי החלטת המפתחת)
- הצפנת טבלאות אחרות בפרויקט (`SeizureLog`, `FoodLog`, נתוני תרופות) — פרויקט נפרד עתידי.
- Moderation, סינון תוכן, הגבלת קצב הודעות מחודשת — פריט נפרד ברשימת הפיצ'ר המלאה.
- Safety Admin, de-anonymization, Audit Log — פריטים נפרדים עתידיים.
- טיפול בניתוק WebSocket מכל סיבה **שאינה** קוד 4000 — מוזכר במפורש כלא-מטופל כרגע (ראו סעיף Risks).
- מערכת התרעות (alerting) על אי-ריצת ה-job — שלב עתידי מתקדם.
- הקמת AWS Secrets Manager / External Secrets Operator — שיפור עתידי אפשרי, לא כאן.

### Mandatory
כל מה שברשימת "In Scope" למעלה.

### Optional
אין פריטים אופציונליים בסקופ הזה — כל מה שסוכם הוגדר כחובה לשלד הבסיסי.

## 4. Engineering Decisions

| # | החלטה | הבחירה | מקור |
|---|---|---|---|
| 1 | מודל שמירה תקופתי | Job יומי קבוע ב-23:59 Asia/Jerusalem, לא TTL מתגלגל של 24 שעות לכל הודעה | Developer Decision |
| 2 | מה נמחק ב-job | גם `ChatMessage` וגם `PseudonymAssignment` של אותו יום, יחד | Developer Decision |
| 3 | ניתוק בזמן ה-job | כל המחוברים לחדר מנותקים בכוח, קוד סגירה 4000, בלי הודעת מערכת גלויה | Developer Decision |
| 4 | תגובת קליינט לקוד 4000 | Redirect שקט לעמוד הבית | Developer Decision |
| 5 | תגובת קליינט לקודי ניתוק אחרים | ללא טיפול כרגע — מתועד כפער מכוון, לא נשכח | Developer Decision |
| 6 | שדה `chat_day` ב-`ChatMessage` | נשמר (למרות שלא נדרש לסינון בפועל, לצורך debugging עתידי) | Developer Decision |
| 7 | ייצוג כינוי בהודעה | מחרוזת "צילום מצב" (snapshot), לא קישור (FK) ל-`PseudonymAssignment` | Developer Decision, מבוסס על החלטה 2 |
| 8 | מחיקת משתמש → מה קורה להודעותיו | `on_delete=SET_NULL` (ההודעה נשארת, הקישור לחשבון מתנתק) | Developer Decision |
| 9 | Constraints על `ChatMessage` | ללא UNIQUE/CHECK — הודעות מרובות מאותו משתמש/חדר/יום הן תקינות | Developer Decision |
| 10 | Index | מורכב על `(room_name, created_at)` לתמיכה בשאילתת ההיסטוריה | Developer Decision |
| 11 | תזמון Celery | `CELERY_BEAT_SCHEDULE` סטטי ב-`settings.py`, לא `django-celery-beat` | Developer Decision |
| 12 | Result backend ל-Celery | ללא — לוגים בלבד, מספיק לשלד בסיסי | Developer Decision |
| 13 | ספריית הצפנה | עטיפה עצמאית דקה מעל `cryptography` (כבר תלות קיימת בפרויקט), לא ספריית Django-wrapper צד-שלישי | Developer Decision, מבוסס על בדיקת תאימות ל-Django 5.1 |
| 14 | אחסון מפתח הצפנה | `CHAT_MESSAGE_ENCRYPTION_KEY`, בתוך `django-secrets` הקיים | Developer Decision, Existing System pattern |
| 15 | עימוד היסטוריה | 10 הודעות לעמוד, מהחדש לישן | Developer Decision |
| 16 | טעינת עמודים נוספים | גלילה אוטומטית (infinite scroll), לא כפתור | Developer Decision |
| 17 | תשתית Celery | להקים מאפס — לא קיימת היום | Existing System (gap) |

## 5. Technology Stack

ללא שינוי מהקיים, בתוספת:
- **Celery Beat** (סטטי, בתוך תהליך ה-worker/beat הקיים בהגדרה אך טרם פרוס).
- **`cryptography`** (Fernet) — כבר תלות קיימת, שימוש חדש.

אין ספריות Django-wrapper חדשות (`django-fernet-fields` וכדומה נשקלו ונדחו — ראו החלטה 13).

## 6. High-Level Architecture

```
Client (room.html)
   │  WebSocket
   ▼
ChatConsumer (MindedHealth/consumers.py)
   │  connect(): auth → role/room check → pseudonym → [NEW] send first history page
   │  receive(): [NEW] branch: "load_history" action → send older page
   │             else: existing chat-message flow → [NEW] persist ChatMessage (encrypted) → broadcast
   │
   ▼
PostgreSQL/SQLite: ChatMessage, PseudonymAssignment
   ▲
   │  daily at 23:59 Asia/Jerusalem
Celery Beat → Celery task (chat/tasks.py)
   │  delete ChatMessage + PseudonymAssignment for the day
   │  channel_layer.group_send(room, {"type": "day_ended"}) → each connected consumer closes (code 4000)
```

## 7. Database Design

### Entity: `ChatMessage`

| שדה | סוג | Required/Nullable | ברירת מחדל |
|---|---|---|---|
| `id` | BigAutoField (PK) | Required | auto |
| `user` | ForeignKey → `settings.AUTH_USER_MODEL`, `on_delete=SET_NULL` | **Nullable** | — |
| `pseudonym` | CharField(max_length=50) | Required | — |
| `room_name` | CharField(max_length=100) | Required | — |
| `chat_day` | DateField | Required | — |
| `content` | טקסט מוצפן (Fernet, דרך עטיפה מותאמת מעל `cryptography`) | Required | — |
| `created_at` | DateTimeField | Required | `auto_now_add=True` |

**Constraints:** אין (לא UNIQUE, לא CHECK).
**Indexes:** `models.Index(fields=["room_name", "created_at"])`.

### Entity: `PseudonymAssignment` (קיים — שינוי התנהגות בלבד, לא סכימה)

אין שינוי במבנה. שינוי יחיד: שורות של יום שהסתיים נמחקות על-ידי אותו Celery task שמנקה את `ChatMessage`.

## 8. API Contracts (WebSocket message shapes)

**קיים, ללא שינוי:**
- Client → Server: `{"message": "<text>"}` — הודעת צ'אט רגילה.
- Server → Client (על כל מחובר): `{"type": "your_pseudonym", "pseudonym": "..."}`.
- Server → Client (broadcast): `{"users": [...]}`.
- Server → Client (broadcast הודעה): `{"message": "...", "user": "<pseudonym>", "time": "..."}`.

**חדש:**
- Client → Server (בקשת עמוד היסטוריה נוסף): `{"action": "load_history", "before_id": <int>}`. בטעינה הראשונית (connect), השרת שולח את העמוד הראשון **מיוזמתו**, ללא צורך שהקליינט יבקש.
- Server → Client (עמוד היסטוריה): `{"type": "history", "messages": [{"pseudonym": "...", "message": "...", "time": "..."}, ...], "has_more": true|false}`. הודעות בתוך כל עמוד מוחזרות בסדר ישן-לחדש (למרות שהשאילתה עצמה מהחדש-לישן) כדי שהקליינט יוכל להוסיף אותן ישירות לתחילת הרשימה בלי היפוך נוסף.
- Server → Client (ניתוק כפוי בסוף יום): סגירת WebSocket עם close code **4000**, ללא payload.

## 9. External Integrations

אין אינטגרציה חיצונית חדשה. Redis (channel layer, קיים) ו-PostgreSQL (קיים) בלבד.

## 10. Infrastructure

- **Celery Worker + Beat:** אינם קיימים כלל היום בפריסה (`k8s/`) — יש להקים deployment חדש. **לא כלול בביצוע עכשיו** — חסום עד לגישת AWS (ראו סעיף Deployment Strategy).
- **K8s Secret:** תוספת מפתח `CHAT_MESSAGE_ENCRYPTION_KEY` ל-`django-secrets` הקיים.

## 11. Deployment Strategy

**המצב הנוכחי (בזמן כתיבת מסמך זה):** אין גישת AWS/Kubernetes בכלל למפתחת (חשבון root נעול, ticket פתוח מול AWS Support, אין מפתחות IAM חלופיים, אין kubeconfig מקומי).

**המשמעות לתוכנית:**
- **שלב א' — קוד ובדיקות (לא חסום, ניתן להתחיל מיד):** כל הקוד (מודלים, migration, שינויי consumer, Celery task, הצפנה, שינויי תבנית, בדיקות) נכתב ונבדק מקומית במלואו.
- **שלב ב' — פריסה (חסום עד חזרת גישת AWS):**
  1. יצירת/עדכון `django-secrets` עם `CHAT_MESSAGE_ENCRYPTION_KEY`.
  2. פריסת Celery worker + Beat לראשונה אי-פעם ל-cluster.
  3. `kubectl apply` על ה-manifests המעודכנים.
  4. `kubectl rollout restart` לפודי Django.

הגבול בין שלב א' לשלב ב' חייב להישאר ברור בזמן ביצוע — שלב א' יכול להתקדם עכשיו במלואו.

## 12. Execution Strategy

עבודה בסדר תלויות: קודם סכימת DB (migration), אחר כך שינויי consumer שתלויים בה, אחר כך תשתית Celery, אחר כך הצפנה (יכולה להיכתב במקביל לחלקים אחרים כי היא מבודדת יחסית), ולבסוף שינויי תבנית/JS בצד הלקוח.

## 13. Execution Order

1. **מודל `ChatMessage` + migration**
   - Goal: לבסס את שכבת האחסון.
   - Deliverable: `chat/models.py` מעודכן, migration חדש.
   - Dependencies: אין.
   - Definition of Done: `manage.py makemigrations --check` נקי, migration רץ מקומית.

2. **עטיפת הצפנה (`cryptography`/Fernet) + חיבור לשדה `content`**
   - Goal: תוכן ההודעה מוצפן ב-DB.
   - Deliverable: מודול הצפנה קטן ב-`chat/`, אינטגרציה עם `ChatMessage.content`.
   - Dependencies: שלב 1.
   - Definition of Done: כתיבה/קריאה של הודעה מוצפנת ומפוענחת נכון בבדיקה.

3. **תשתית Celery מאפס**
   - Goal: אפליקציית Celery קיימת ועובדת מקומית.
   - Deliverable: `MindedHealth/celery.py`, חיווט ב-`MindedHealth/__init__.py`, `CELERY_BEAT_SCHEDULE` ב-`settings.py`.
   - Dependencies: אין (עצמאי).
   - Definition of Done: `celery -A MindedHealth worker` עולה מקומית בלי שגיאות.

4. **Celery task יומי**
   - Goal: מימוש הלוגיקה של מחיקה + ניתוק.
   - Deliverable: `chat/tasks.py` — מוחק `ChatMessage` ו-`PseudonymAssignment` של היום, שולח `day_ended` דרך channel layer.
   - Dependencies: שלבים 1, 3.
   - Definition of Done: בדיקה שמריצה את ה-task ידנית ומוודאת מחיקה + ניתוק consumer מבודד (in-memory channel layer).

5. **`ChatConsumer.receive()` — שמירת הודעות + branching ל-load_history**
   - Goal: כל הודעה שנשלחת גם נשמרת; תמיכה בבקשת עמוד היסטוריה נוסף.
   - Deliverable: `MindedHealth/consumers.py` מעודכן.
   - Dependencies: שלבים 1, 2.
   - Definition of Done: בדיקת consumer קיימת ממשיכה לעבור + בדיקה חדשה שמוודאת שמירה בפועל.

6. **`ChatConsumer.connect()` — שליחת עמוד היסטוריה ראשוני + טיפול ב-`day_ended`**
   - Goal: משתמש שמתחבר רואה היסטוריה; consumer מגיב לניתוק כפוי.
   - Deliverable: `MindedHealth/consumers.py` מעודכן (המשך לשלב 5).
   - Dependencies: שלבים 1, 4.
   - Definition of Done: בדיקה שמוודאת קבלת עמוד היסטוריה ראשון עם החיבור.

7. **`templates/chat/room.html` — גלילה אוטומטית + טיפול ב-close code 4000**
   - Goal: חוויית משתמש מלאה בצד הלקוח.
   - Deliverable: JS מעודכן.
   - Dependencies: שלבים 5, 6.
   - Definition of Done: נבדק ידנית מול שרת מקומי (הדגמה חזותית, לא רק טסט).

8. **תיעוד "פער מכוון"**
   - Goal: לוודא שהיעדר טיפול בקודי ניתוק אחרים לא נשכח.
   - Deliverable: הערה בקוד + רישום ברשימת המשימות העתידיות (מעבר למסמך זה).
   - Dependencies: שלב 7.
   - Definition of Done: מתועד במקום גלוי.

9. **פריסה** (חסום עד גישת AWS — ראו סעיף 11)

## 14. Capability Breakdown

- **Capability: Message Storage** (שלבים 1–2)
- **Capability: Scheduled Retention** (שלבים 3–4)
- **Capability: History Delivery** (שלבים 5–6–7)
- **Capability: Deployment Readiness** (שלב 9, חסום)

## 15. Definition of Done

- כל 6 השלבים הראשונים (1–6) מיושמים, עם בדיקות `pytest` ירוקות (`chat/tests/`), כולל הרצה אמיתית של WebSocket (`channels.testing.WebsocketCommunicator` + `InMemoryChannelLayer`, לא Redis אמיתי — תואם למוסכמת הבדיקות הקיימת).
- שלב 7 (JS) נבדק ידנית מול שרת מקומי.
- `manage.py check` ו-`makemigrations --check` נקיים.
- אין קוד שמבצע פעולות פריסה בפועל (שלב 9 נשאר תיאורטי עד גישת AWS).

## 16. Timeline

מסמך זה **אינו** קובע לוח זמנים או אבני דרך (milestones) — זה מחוץ לתפקיד של שלב התכנון הזה. פירוק ל-milestones בפועל הוא באחריות המפתחת, על בסיס סדר הביצוע (סעיף 13).

## 17. Risks

| סיכון | תיאור |
|---|---|
| ניתוק WebSocket מסיבה שאינה 4000 | נשאר ללא טיפול בכוונה (החלטה 5) — משתמש עם נפילת רשת רגעית יישאר עם מסך "תקוע" בלי משוב. מתועד כפער מוכר, לא תקלה. |
| Job לא רץ כלל | ללא alerting (החלטה 12) — אם Celery Beat נופל, לא תהיה שום התרעה. תלוי בבדיקה ידנית/לוגים בלבד. |
| תאימות ספריית הצפנה חיצונית | נמנע ע"י בחירה בעטיפה עצמאית מעל `cryptography` (החלטה 13) — מקטין את הסיכון, לא מבטל תלות בעדכוני הספרייה הבסיסית. |
| פריסה ראשונה של Celery ל-K8s | תשתית חדשה שמעולם לא הופעלה בפרודקשן — סיכון תפעולי בפעם הראשונה שהיא רצה בסביבה אמיתית, מעבר לבדיקות מקומיות. |
| מפתח הצפנה אבוד/לא זמין | אם `CHAT_MESSAGE_ENCRYPTION_KEY` יאבד, כל התוכן המוצפן הקיים הופך לבלתי-קריא. מוקטן משמעותית ע"י כך שההודעות ממילא נמחקות תוך פחות מיום. |

## 18. Risk Mitigation

- ניתוק ללא 4000: תועד במפורש (החלטה 5, סעיף Out of Scope) כפריט שידרש טיפול נפרד — לא "נשכח בשקט".
- אי-ריצת job: לוגים ברורים בתחילת/סוף ריצה (כבר בתוכנית, שלב 4) כבסיס מינימלי; alerting מלא מתועד כ-Out of Scope מפורש לעתיד.
- הצפנה: שימוש בפונקציונליות מבוססת (Fernet מתוך `cryptography`) ולא קוד הצפנה מומצא.
- פריסת Celery: מבוצעת ונבדקת מקומית באופן מלא לפני שהיא נוגעת בפרודקשן כלל (שלב 9 מופרד לגמרי).

## 19. Decision Traceability

כל 17 ההחלטות בסעיף 4 מגיעות מ-**Developer Decision** (הוחלטו ישירות בשיחה אינטראקטיבית עם המפתחת), פרט ל-#14 ו-#17 שמסומנות גם כ-**Existing System** (תבנית זהה למה שכבר קיים בפרויקט — `openai-secret`, ו-`CELERY_BROKER_URL` המוגדר-אך-לא-מחווט). אין אף החלטה שמסומנת "Assumption" במסמך הסופי — כל נקודה שהייתה עמומה הועלתה ונענתה.

## 20. Planning Validation Checklist

- [x] כל דרישה מהדיון (Feature Discovery + כל שלב תכנון) מכוסה במסמך.
- [x] כל deliverable חובה מופיע ב-Execution Order.
- [x] אין פריט אופציונלי לפני פריט חובה.
- [x] לכל החלטה יש מקור מתועד (סעיף 19).
- [x] אין הנחה שמוצגת כעובדה — כל נקודה עמומה עברה דרך שאלת הבהרה מפורשת.
- [x] התוכנית ניתנת לביצוע ישיר (מספיק פירוט לכל שלב ב-Execution Order).
- [x] מוכן למסירה לשלב פירוק ל-capabilities/milestones בפועל.

---

## נספח: מנגנון הגלילה האוטומטית (Infinite Scroll) — הסבר להצגה/דיבור

תוסף למסמך, נכתב אחרי המימוש (PR 3), כדי שיהיה אפשר להסביר את המנגנון בלי לחזור לקוד.

### שלושה משתנים בצד הלקוח (`templates/chat/room.html`)

| משתנה | תפקיד |
|---|---|
| `oldestMessageId` | ה-ID של ההודעה **הכי ישנה** שמוצגת כרגע על המסך |
| `hasMoreHistory` | האם יש עוד הודעות ישנות יותר שעדיין לא נטענו |
| `isLoadingHistory` | "מנעול" זמני — מונע בקשת אותו עמוד פעמיים במקביל |

### מתי זה מופעל

יש מאזין (`addEventListener('scroll', ...)`) על תיבת ההודעות. בכל גלילה נבדק: האם המשתמש הגיע ממש לראש התיבה (`scrollTop === 0`) **וגם** יש עוד היסטוריה **וגם** אין כרגע טעינה פעילה? אם כן — נשלחת לשרת בקשה `{"action": "load_history", "before_id": <oldestMessageId>}`.

### הטריק לשמירת מיקום הגלילה

בעיה: אם פשוט "מדביקים" הודעות ישנות בראש התיבה, המסך "קופץ" ומבלבל את הקורא. הפתרון (תבנית סטנדרטית להוספת תוכן בראש אזור גלילה):

1. לפני ההוספה — שומרים את הגובה הנוכחי של כל התיבה: `const previousHeight = chatLog.scrollHeight;`
2. מוסיפים את ההודעות החדשות **בראש** הטקסט הקיים.
3. מזיזים את מיקום הגלילה בדיוק בהפרש: `chatLog.scrollTop = chatLog.scrollHeight - previousHeight;`

התוצאה: המשתמש נשאר מסתכל על **אותה הודעה בדיוק** שהיה עליה לפני הטעינה — רק שעכשיו יש תוכן נוסף מעליה, זמין לגלילה נוספת.

### זרימה מלאה (מה-connect ועד גלילה)

1. חיבור ל-חדר → שרת שולח אוטומטית עמוד ראשון (10 הודעות אחרונות, מהישן לחדש בתוך העמוד) עם `type: "history"`.
2. הלקוח ממלא את `oldestMessageId` מההודעה הראשונה בעמוד, ואת `hasMoreHistory` מהשדה `has_more`.
3. משתמש גולל למעלה → אם `hasMoreHistory` נכון, נשלחת בקשת `load_history` עם ה-`before_id` הנוכחי.
4. השרת מחזיר את העמוד הבא (10 הודעות ישנות יותר, עדיין מהישן לחדש בתוך העמוד) — הלקוח מוסיף אותן בראש, בעזרת הטריק לשמירת מיקום הגלילה, ומעדכן שוב את `oldestMessageId` ו-`hasMoreHistory`.
5. כשה-`has_more` מגיע `false` — הגלילה למעלה כבר לא מפעילה עוד בקשות (כי `hasMoreHistory` הוא `false`).
