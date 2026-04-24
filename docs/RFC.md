# RFC: Halo Inventory — Intézményi Eszköznyilvántartó Rendszer

**Date:** 2026-04-24
**Status:** Draft
**Author:** Dávid Nagy
**Audience:** Engineering team and coding agents

---

## 1. Overview

### 1.1 Goal

Szociális és gyermekjóléti intézmény (~7 telephely) technikai eszközeinek teljes életciklus-kezelése: felvétel, módosítás, QR-kódos azonosítás, periodikus audit (leltárellenőrzés) és selejtezés. A rendszer megteremti az intézmény jogszerű és visszakövethető eszköznyilvántartásának alapját.

### 1.2 In Scope

- Telephely-kezelés (CRUD)
- Eszköz CRUD + soft-delete selejtezéssel
- QR-kód generálás minden eszközhöz, PNG export nyomtatáshoz
- Audit session indítása telephelyhez, hibrid ellenőrzés (QR scan + kézi tick-off)
- Audit riport: megvan / hiányzik / nem ellenőrzött bontásban, letölthetően
- Eszközlista Excel export (szűrve, illetve selejtezett eszközök külön)
- JWT-alapú autentikáció (access + refresh token)
- Szerepköralapú jogosultságkezelés (director, delegate)
- Felhasználókezelés (director hatásköre)
- Deployment: Render.com cloud platform

### 1.3 Out of Scope

- Pénzügyi / számviteli modul (bszerezési ár, értékcsökkentés, leltárérték)
- Garancia-kezelés és szerviz előzmények
- Email értesítések
- Natív mobilalkalmazás (a frontend PWA-barát, de önálló app nem)
- Jogi megfelelőség automatizálása (a rendszer puszta létezése előrelépés)
- Vonalkód-leolvasó eszköz integrációja

### 1.4 Source of Truth Policy

Dokumentum vs. kód konfliktus esetén: **ez a dokumentum nyeri**. A kódot kell frissíteni, nem a dokumentumot. Kivétel: ha egy szekció `// SUPERSEDED BY D-NNN` jelöléssel van ellátva, a döntési napló bejegyzése érvényes.

---

## 2. Requirements

> Minden R-* ID megjelenik a Section 17 RFC Manifest `requirements` tömbjében.

**R-001** [MUST] A rendszernek MUST lehetővé tennie eszköz felvételét a következő kötelező mezőkkel: név, kategória, telephely. Opcionális: gyártó, modell, sorozatszám, szoba, felelős dolgozó neve.

**R-002** [MUST] A rendszernek MUST lehetővé tennie eszköz bármely mezőjének módosítását (kivéve: id, qr_code, created_at, created_by_id).

**R-003** [MUST] A rendszernek MUST lehetővé tennie eszköz selejtezését soft-delete mechanizmussal: az eszköz `retired` státuszba kerül, megőrzi teljes adatát és előzményét. A selejtezéskor ok megadása kötelező.

**R-004** [MUST] Eszköz létrehozásakor a rendszernek MUST automatikusan QR-kódot generálnia UUID tartalmú szöveggel (`halo-inv://{equipment_uuid}` sémában).

**R-005** [MUST] A rendszernek MUST lehetővé tennie az eszköz QR-kódjának PNG formátumban való letöltését nyomtatás céljából. A PNG-n szerepeljen: QR kép, eszköz neve, telephely neve, sorozatszám (ha van).

**R-006** [MUST] A rendszernek MUST lehetővé tennie audit session indítását egy adott telephelyhez. Az indításkor a rendszer automatikusan felveszi az összes aktív (`active` státuszú) eszközt a telephelyről `not_checked` állapottal.

**R-007** [MUST] Aktív audit session során a rendszernek MUST lehetővé tennie eszköz jelenlétének rögzítését QR-kód beolvasásával telefonos kamera segítségével.

**R-008** [MUST] Aktív audit session során a rendszernek MUST lehetővé tennie eszköz kézi megjelölését (jelen van / hiányzik) QR-kód nélkül is.

**R-009** [MUST] Audit lezárásakor a rendszernek MUST riportot generálnia, amely tartalmazza: ellenőrzött és jelen lévő eszközök listája, hiányzó eszközök listája, nem ellenőrzött eszközök listája, és összesítő számok.

**R-010** [MUST] A rendszernek MUST JWT-alapú autentikációt alkalmaznia. A login access tokent (15 perces lejárat) és refresh tokent (7 napos lejárat) ad vissza. A refresh token felhasználható új access token igénylésére.

**R-011** [MUST] A rendszernek MUST két szerepkört támogatnia: `director` (intézményvezető, teljes hozzáférés + felhasználókezelés) és `delegate` (megbízott, teljes hozzáférés, felhasználókezelés nélkül).

**R-012** [SHOULD] Az eszközlistának SHOULD szűrhetőnek lennie telephely, kategória és státusz (active/retired) alapján.

**R-013** [SHOULD] Az audit riportnak SHOULD letölthetőnek lennie JSON vagy PDF formátumban.

**R-014** [MAY] A rendszer MAY megjeleníthet telephely-szintű összesítő dashboardot (eszközök száma kategóriánként, utolsó audit dátuma).

**R-015** [SHOULD] Az eszközlistának SHOULD exportálhatónak lennie Excel (.xlsx) formátumban, az aktuális szűrési feltételekkel.

**R-016** [SHOULD] A selejtezett eszközöknek SHOULD exportálhatónak lenniük külön Excel fájlba számviteli felhasználásra.

---

## 3. Domain Model

### 3.1 Entities

#### Location

| Field | Type | Nullable | Constraints |
|---|---|---|---|
| id | uuid | NO | PRIMARY KEY |
| name | varchar(100) | NO | UNIQUE |
| address | text | YES | |
| created_at | timestamptz | NO | DEFAULT now() |
| updated_at | timestamptz | NO | DEFAULT now() |

**Relationships:**
- Location has many Equipment via `equipment.location_id`
- Location has many AuditSession via `audit_sessions.location_id`

---

#### User

| Field | Type | Nullable | Constraints |
|---|---|---|---|
| id | uuid | NO | PRIMARY KEY |
| email | varchar(255) | NO | UNIQUE |
| full_name | varchar(100) | NO | |
| role | enum('director','delegate') | NO | |
| is_active | boolean | NO | DEFAULT true |
| password_hash | varchar(255) | NO | |
| created_at | timestamptz | NO | DEFAULT now() |
| updated_at | timestamptz | NO | DEFAULT now() |

**Relationships:**
- User creates many Equipment via `equipment.created_by_id`
- User retires many Equipment via `equipment.retired_by_id`
- User starts many AuditSession via `audit_sessions.started_by_id`

---

#### Equipment

| Field | Type | Nullable | Constraints |
|---|---|---|---|
| id | uuid | NO | PRIMARY KEY |
| name | varchar(150) | NO | |
| category | enum | NO | VALUES: 'laptop','desktop','printer','phone','tablet','monitor','projector','other' |
| manufacturer | varchar(100) | YES | |
| model | varchar(100) | YES | |
| serial_number | varchar(100) | YES | UNIQUE WHERE NOT NULL |
| qr_code | varchar(36) | NO | UNIQUE |
| location_id | uuid | NO | FK → locations.id ON DELETE RESTRICT |
| room | varchar(100) | YES | |
| assigned_to | varchar(100) | YES | |
| status | enum('active','retired') | NO | DEFAULT 'active' |
| retired_at | timestamptz | YES | |
| retired_by_id | uuid | YES | FK → users.id ON DELETE SET NULL |
| retirement_reason | text | YES | |
| created_at | timestamptz | NO | DEFAULT now() |
| updated_at | timestamptz | NO | DEFAULT now() |
| created_by_id | uuid | NO | FK → users.id ON DELETE RESTRICT |

**Relationships:**
- Equipment belongs to Location via `location_id`
- Equipment belongs to User (creator) via `created_by_id`
- Equipment belongs to User (retiree) via `retired_by_id`
- Equipment has many AuditItem via `audit_items.equipment_id`

**Enum: category storage values**
| Display | Stored value |
|---|---|
| Laptop | laptop |
| Asztali számítógép | desktop |
| Nyomtató | printer |
| Telefon | phone |
| Tablet | tablet |
| Monitor | monitor |
| Projektor | projector |
| Egyéb | other |

---

#### AuditSession

| Field | Type | Nullable | Constraints |
|---|---|---|---|
| id | uuid | NO | PRIMARY KEY |
| location_id | uuid | NO | FK → locations.id ON DELETE RESTRICT |
| started_by_id | uuid | NO | FK → users.id ON DELETE RESTRICT |
| started_at | timestamptz | NO | DEFAULT now() |
| completed_at | timestamptz | YES | |
| status | enum('in_progress','completed') | NO | DEFAULT 'in_progress' |
| notes | text | YES | |

**Relationships:**
- AuditSession belongs to Location via `location_id`
- AuditSession belongs to User via `started_by_id`
- AuditSession has many AuditItem via `audit_items.audit_session_id`

**Business rule:** Egy telephelyen egyszerre csak egy `in_progress` státuszú audit session létezhet. Új session indításakor 409 Conflict, ha már van nyitott session.

---

#### AuditItem

| Field | Type | Nullable | Constraints |
|---|---|---|---|
| id | uuid | NO | PRIMARY KEY |
| audit_session_id | uuid | NO | FK → audit_sessions.id ON DELETE CASCADE |
| equipment_id | uuid | NO | FK → equipment.id ON DELETE RESTRICT |
| check_method | enum('scan','manual') | YES | NULL = még nem ellenőrzött |
| checked_at | timestamptz | YES | NULL = még nem ellenőrzött |
| is_present | boolean | YES | NULL = nem ellenőrzött, TRUE = megvan, FALSE = hiányzik |

**Uniqueness:** `(audit_session_id, equipment_id)` UNIQUE — egy eszköz egy sessionban csak egyszer szerepelhet.

**Relationships:**
- AuditItem belongs to AuditSession
- AuditItem belongs to Equipment

---

### 3.2 Indexes

| Table | Index | Type |
|---|---|---|
| equipment | (location_id, status) | BTREE |
| equipment | (qr_code) | BTREE UNIQUE |
| equipment | (serial_number) WHERE serial_number IS NOT NULL | PARTIAL UNIQUE |
| audit_sessions | (location_id, status) | BTREE |
| audit_sessions | (status) WHERE status = 'in_progress' | PARTIAL |
| audit_items | (audit_session_id, equipment_id) | BTREE UNIQUE |

---

## 4. Authorization Model

### 4.1 Roles

| Role | Leírás |
|---|---|
| `director` | Intézményvezető. Teljes hozzáférés minden adathoz és művelethez, beleértve a felhasználókezelést. |
| `delegate` | Megbízott. Teljes hozzáférés eszközökhöz, telephelyekhez és auditokhoz. Felhasználókezeléshez nincs joga. |

### 4.2 Permission Matrix

| Permission | director | delegate |
|---|---|---|
| locations:read | ✓ | ✓ |
| locations:write | ✓ | ✓ |
| equipment:read | ✓ | ✓ |
| equipment:write | ✓ | ✓ |
| equipment:retire | ✓ | ✓ |
| equipment:export | ✓ | ✓ |
| audits:read | ✓ | ✓ |
| audits:write | ✓ | ✓ |
| users:read | ✓ | ✗ |
| users:write | ✓ | ✗ |

### 4.3 Auth Behavior

- **401 Unauthenticated:** access token hiányzik vagy érvénytelen
- **403 Unauthorized:** token érvényes, de a szerepkör nem rendelkezik a szükséges jogosultsággal
- **Anonymous:** egyetlen endpoint sem elérhető autentikáció nélkül, kivéve `POST /api/v1/auth/login`

---

## 5. API Contract

**Base path:** `/api/v1`

Minden védett endpoint megköveteli az `Authorization: Bearer <access_token>` headert.

---

### 5.1 Auth

#### POST /auth/login

- **Auth:** anonymous
- **Request body:**
  ```json
  { "email": "string", "password": "string" }
  ```
- **Response 200:**
  ```json
  { "access_token": "string", "refresh_token": "string", "token_type": "bearer" }
  ```
- **Response 401:** invalid credentials
- **Requirement refs:** R-010

#### POST /auth/refresh

- **Auth:** anonymous (refresh token in body)
- **Request body:** `{ "refresh_token": "string" }`
- **Response 200:** `{ "access_token": "string", "token_type": "bearer" }`
- **Response 401:** invalid or expired refresh token
- **Requirement refs:** R-010

#### POST /auth/logout

- **Auth:** required
- **Request body:** `{ "refresh_token": "string" }`
- **Response 204:** no content
- **Requirement refs:** R-010

---

### 5.2 Locations

#### GET /locations

- **Auth:** required
- **Permission:** locations:read
- **Response 200:** `{ "items": [Location], "total": int }`
- **Requirement refs:** R-014

#### POST /locations

- **Auth:** required
- **Permission:** locations:write
- **Request body:** `{ "name": "string", "address": "string|null" }`
- **Response 201:** Location object
- **Response 409:** name already exists
- **Requirement refs:** R-011

#### GET /locations/{id}

- **Auth:** required
- **Permission:** locations:read
- **Response 200:** Location object + `equipment_count: int`
- **Response 404:** not found
- **Requirement refs:** R-014

#### PUT /locations/{id}

- **Auth:** required
- **Permission:** locations:write
- **Request body:** `{ "name": "string", "address": "string|null" }`
- **Response 200:** updated Location
- **Response 404 / 409:** standard
- **Requirement refs:** R-011

#### DELETE /locations/{id}

- **Auth:** required
- **Permission:** locations:write
- **Response 204:** deleted
- **Response 409:** location has active equipment (MUST NOT delete)
- **Requirement refs:** R-011

---

### 5.3 Equipment

#### GET /equipment

- **Auth:** required
- **Permission:** equipment:read
- **Query params:** `location_id`, `category`, `status` (default: active), `page`, `page_size` (default 50, max 200)
- **Response 200:** `{ "items": [Equipment], "total": int, "page": int, "page_size": int }`
- **Requirement refs:** R-001, R-012

#### POST /equipment

- **Auth:** required
- **Permission:** equipment:write
- **Request body:**
  ```json
  {
    "name": "string",
    "category": "laptop|desktop|printer|phone|tablet|monitor|projector|other",
    "location_id": "uuid",
    "manufacturer": "string|null",
    "model": "string|null",
    "serial_number": "string|null",
    "room": "string|null",
    "assigned_to": "string|null"
  }
  ```
- **Response 201:** Equipment object (beleértve a generált `qr_code` mezőt)
- **Response 409:** serial_number ütközés
- **Response 422:** validációs hiba
- **Requirement refs:** R-001, R-004

#### GET /equipment/{id}

- **Auth:** required
- **Permission:** equipment:read
- **Response 200:** teljes Equipment object
- **Response 404:** not found
- **Requirement refs:** R-001

#### PUT /equipment/{id}

- **Auth:** required
- **Permission:** equipment:write
- **Request body:** ugyanaz mint POST, minden mező opcionális (partial update)
- **Response 200:** updated Equipment
- **Response 404 / 409 / 422:** standard
- **Requirement refs:** R-002

#### POST /equipment/{id}/retire

- **Auth:** required
- **Permission:** equipment:retire
- **Request body:** `{ "reason": "string" }` — reason kötelező, min. 5 karakter
- **Response 200:** updated Equipment (status=retired)
- **Response 409:** already retired
- **Requirement refs:** R-003

#### GET /equipment/{id}/qr

- **Auth:** required
- **Permission:** equipment:read
- **Response 200:** `Content-Type: image/png` — QR kód PNG kép (400×400px), alján: eszköz neve, telephely neve, sorozatszám
- **Requirement refs:** R-004, R-005

#### GET /equipment/export

- **Auth:** required
- **Permission:** equipment:export
- **Query params:** `location_id`, `category`, `status` (same as list endpoint)
- **Response 200:** `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` — Excel fájl
- **Filename header:** `Content-Disposition: attachment; filename="equipment_export_{date}.xlsx"`
- **Excel columns:** Név, Kategória, Gyártó, Modell, Sorozatszám, Telephely, Szoba, Felelős, Státusz, Selejtezés oka, Selejtezés dátuma, Létrehozva
- **Requirement refs:** R-015, R-016

---

### 5.4 Audit

#### POST /audits

- **Auth:** required
- **Permission:** audits:write
- **Request body:** `{ "location_id": "uuid", "notes": "string|null" }`
- **Behavior:** Session létrehozása, majd az adott telephely összes `active` eszközéhez AuditItem létrehozása `is_present=null` értékkel. Atomikusan (tranzakcióban).
- **Response 201:** AuditSession object + `item_count: int`
- **Response 409:** már van nyitott (`in_progress`) session ehhez a telephelyhez
- **Requirement refs:** R-006

#### GET /audits

- **Auth:** required
- **Permission:** audits:read
- **Query params:** `location_id`, `status`, `page`, `page_size`
- **Response 200:** `{ "items": [AuditSession], "total": int }`
- **Requirement refs:** R-006

#### GET /audits/{id}

- **Auth:** required
- **Permission:** audits:read
- **Response 200:**
  ```json
  {
    "session": AuditSession,
    "summary": { "total": int, "present": int, "missing": int, "unchecked": int },
    "items": [AuditItem + equipment snapshot]
  }
  ```
- **Requirement refs:** R-006, R-009

#### POST /audits/{id}/scan

- **Auth:** required
- **Permission:** audits:write
- **Request body:** `{ "qr_code": "string" }` — a QR kód teljes tartalma (`halo-inv://{uuid}`)
- **Behavior:** UUID kinyerése, eszköz megkeresése, `is_present=true`, `check_method='scan'`, `checked_at=now()` beállítása
- **Response 200:** frissített AuditItem
- **Response 404:** eszköz nem található ezzel a QR kóddal
- **Response 409:** session már lezárt, vagy az eszköz nem tartozik ehhez a telephelyhez
- **Requirement refs:** R-007

#### POST /audits/{id}/manual

- **Auth:** required
- **Permission:** audits:write
- **Request body:** `{ "equipment_id": "uuid", "is_present": true|false }`
- **Behavior:** `check_method='manual'`, `checked_at=now()`, `is_present` beállítása
- **Response 200:** frissített AuditItem
- **Response 404:** equipment_id nem szerepel ebben a sessionban
- **Response 409:** session már lezárt
- **Requirement refs:** R-008

#### POST /audits/{id}/complete

- **Auth:** required
- **Permission:** audits:write
- **Request body:** nincs
- **Behavior:** `status='completed'`, `completed_at=now()` beállítása. Nem ellenőrzött itemek `is_present=null` maradnak — ezek kerülnek az "unchecked" listára.
- **Response 200:** lezárt AuditSession
- **Response 409:** session már lezárt
- **Requirement refs:** R-009

#### GET /audits/{id}/report

- **Auth:** required
- **Permission:** audits:read
- **Query params:** `format=json|pdf` (default: json)
- **Response 200 (json):**
  ```json
  {
    "session": AuditSession,
    "location": Location,
    "auditor": { "id": "uuid", "full_name": "string" },
    "summary": { "total": int, "present": int, "missing": int, "unchecked": int },
    "present_items": [Equipment],
    "missing_items": [Equipment],
    "unchecked_items": [Equipment]
  }
  ```
- **Response 200 (pdf):** `Content-Type: application/pdf`, PDF letöltés
- **Response 404:** session nem létezik
- **Response 409:** session még `in_progress` (riport csak lezárt sessionhoz)
- **Requirement refs:** R-009, R-013

---

### 5.5 Users

> Minden `/users` endpoint kizárólag `director` szerepkörrel érhető el.

#### GET /users

- **Auth:** required
- **Permission:** users:read
- **Response 200:** `{ "items": [User (password_hash nélkül)], "total": int }`
- **Requirement refs:** R-011

#### POST /users

- **Auth:** required
- **Permission:** users:write
- **Request body:** `{ "email": "string", "full_name": "string", "role": "director|delegate", "password": "string" }`
- **Response 201:** User object
- **Response 409:** email ütközés
- **Requirement refs:** R-011

#### PUT /users/{id}

- **Auth:** required
- **Permission:** users:write
- **Request body:** `{ "full_name": "string", "role": "director|delegate", "is_active": bool, "password": "string|null" }` — minden opcionális
- **Response 200:** updated User
- **Requirement refs:** R-011

#### DELETE /users/{id}

- **Auth:** required
- **Permission:** users:write
- **Behavior:** soft deactivate — `is_active=false`. Nem fizikai törlés.
- **Response 204:** deactivated
- **Response 409:** saját magát nem deaktiválhatja
- **Requirement refs:** R-011

---

## 6. Error Contract

Minden hiba egységes sémát használ:

```json
{
  "code": "SNAKE_CASE_ERROR_CODE",
  "message": "Human-readable leírás",
  "details": {},
  "trace_id": "uuid"
}
```

| Status | Mikor |
|---|---|
| 400 | Hibás kérés formátum |
| 401 | Nem autentikált (hiányzó/lejárt token) |
| 403 | Autentikált, de nincs joga |
| 404 | Erőforrás nem található |
| 409 | Konfliktus (duplikátum, rossz állapot) |
| 422 | Validációs hiba (Pydantic) |
| 500 | Váratlan szerverhiba |

Példa error code-ok: `EQUIPMENT_NOT_FOUND`, `DUPLICATE_SERIAL_NUMBER`, `AUDIT_SESSION_ALREADY_OPEN`, `EQUIPMENT_ALREADY_RETIRED`, `SELF_DEACTIVATION_FORBIDDEN`

---

## 7. Persistence

- **Database:** PostgreSQL 16 (Render managed)
- **Migration tool:** Alembic
- **Referential integrity:** lásd entity táblák FK szabályai (RESTRICT / CASCADE / SET NULL)
- **Default ordering:**
  - `/equipment`: `name ASC`
  - `/locations`: `name ASC`
  - `/audits`: `started_at DESC`
  - `/audit/{id}` items: `equipment.name ASC`
  - `/users`: `full_name ASC`
- **Pagination:** cursor-free offset pagination; default `page_size=50`, max `200`
- **Soft delete:** `status='retired'` mező — nincs fizikai sorlörlés eszközöknél

---

## 8. Time & Timezone Rules

- Minden timestamp UTC-ben tárolva (timestamptz)
- Minden API válaszban ISO 8601 formátum, Z suffixszel: `2026-04-24T10:00:00Z`
- Frontend felelőssége a helyi idő (Europe/Budapest) megjelenítése
- Semmilyen üzleti logika nem függ időzónától

---

## 9. Concurrency & Atomicity

- `POST /audits`: session létrehozás + AuditItem-ek tömeges beszúrása **egy tranzakcióban** MUST futnia. Hiba esetén rollback.
- `POST /audits/{id}/scan` és `/manual`: `SELECT FOR UPDATE` az AuditItem soron, hogy párhuzamos scan ne okozzon duplikált frissítést.
- `POST /audits/{id}/complete`: idempotens — ha már `completed`, 409 visszaadása, de belső állapot nem változik.
- Egyszerre nyitott audit session per telephely: adatbázisszinten `UNIQUE partial index` biztosítja (`WHERE status = 'in_progress'`).

---

## 10. Observability

- **Health endpoint:** `GET /health` → `{"status": "ok", "db": "ok"}`
- **API docs:** `/docs` (Swagger UI) és `/redoc` fejlesztői környezetben
- **Structured logs:** JSON formátum, mezők: `level`, `message`, `trace_id`, `user_id`, `path`, `method`, `status_code`, `duration_ms`
- **trace_id:** minden request kap UUID trace_id-t (request-scoped), visszaadva error responseban és logban egyaránt
- **Environment config:** minden konfiguráció environment variable-ből, nincs hardcoded érték

| Env var | Leírás |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT aláíró kulcs |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | default: 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | default: 7 |
| `ENVIRONMENT` | `development` / `production` |

---

## 11. Test Requirements

- **Unit tests (pytest):** service réteg teljes lefedettség — legalább happy path + főbb hibautak minden üzleti függvényre
- **API tests (pytest + httpx):** minden endpoint, minden response kód (200/201/204/400/401/403/404/409/422)
- **Audit flow integration test:** session indítás → scan + manual → complete → report teljes folyamat
- **QR export test:** PNG generálás ellenőrzése (fájl méret > 0, PNG magic bytes)
- **Excel export test:** xlsx validáció (openpyxl újraolvasással)
- **E2E (Playwright):** login → eszköz felvétel → QR print oldal → audit flow → riport letöltés
- **Exit criteria:** minden test zöld, 0 skip, 0 ismert regresszió

---

## 12. Backward Compatibility

Új rendszer, nincs korábbi verzió. Backwards compatibility nem alkalmazandó. Az API v1 prefix fenntartja a jövőbeni breaking change lehetőségét.

---

## 13. Implementation Order

1. Database schema és Alembic migrations
2. Pydantic modellek és response sémák
3. Repository réteg (adathozzáférés) minden entitáshoz
4. Service réteg (üzleti logika, QR generálás, Excel export)
5. FastAPI routerek és controllerek
6. JWT auth middleware + role dependency injection
7. Unit és API tesztek (pytest)
8. Next.js frontend:
   - Auth (login, token refresh)
   - Telephely-kezelés
   - Eszköz CRUD + QR print oldal
   - Audit scanner (html5-qrcode kamera integráció)
   - Excel export gombok
9. E2E tesztek (Playwright)

---

## 14. Open Questions

> Nem blokkoló. MVP előtt vagy közben megoldandó.

1. Magyar jogi előírások leltározásra vonatkozóan — az MVP nem foglalkozik ezzel, de ajánlott könyvelővel egyeztetni az üzembehelyezés előtt.

---

## 15. Decision Log

Részletes döntések: `docs/DECISIONS.md`

| ID | Döntés | Indok |
|---|---|---|
| D-001 | Stack: FastAPI + Next.js 14 + PostgreSQL 16 | Python háttér, modern full-stack, jól ismert tooling |
| D-002 | Auth: JWT (access 15 perc + refresh 7 nap) | Stateless, Render.com-on könnyen deployolható |
| D-003 | QR code (nem 1D vonalkód) | Telefon kamerával olvasható, URL-séma hordozható |
| D-004 | Soft delete selejtezésnél | Audit trail megőrzése, visszakereshetőség számvitelhez |
| D-005 | 2 szerepkör: director + delegate | Azonos operatív jogosultság, de elkülönített audit trail és user mgmt hatáskör |
| D-006 | Hibrid audit: scan + kézi tick-off | Ha QR-cimke még nincs felragasztva, kézzel is jelezhető |
| D-007 | Deployment: Render.com cloud | Cold start elfogadható, alacsony traffic, önálló infrastruktúra nem szükséges |
| D-008 | Excel export: openpyxl | Natív Python library, nincs külső függőség |

---

## 16. Deferred Items

> MVP scope-on kívül. Jövőbeni RFC-ben kezelendő.

- Pénzügyi modul: bszerezési ár, számla szám, értékcsökkentés kalkuláció
- Garancia-kezelés: lejárat figyelmeztetés
- Email értesítések (audit elkészült, garancia lejár)
- Natív mobilalkalmazás
- Jogi megfelelőségi riport generálás

---

## 17. RFC Manifest

> **Generated for Architect Agent (agents/02-architect.md).** A `slices` tömböt a Slice Planner Agent tölti ki.

```json
{
  "project": {
    "name": "halo-inventory",
    "domain": "Szociális és gyermekjóléti intézmény eszköznyilvántartás",
    "status": "draft",
    "stack": {
      "frontend": "Next.js 14 (TypeScript)",
      "backend": "FastAPI (Python 3.12)",
      "db": "PostgreSQL 16 (Render managed)",
      "auth": "JWT (access + refresh token)",
      "testing": "pytest, httpx, Playwright"
    }
  },
  "entities": [
    {
      "name": "Location",
      "table": "locations",
      "fields": [
        { "name": "id", "type": "uuid", "nullable": false, "constraints": ["PRIMARY KEY"] },
        { "name": "name", "type": "varchar(100)", "nullable": false, "constraints": ["UNIQUE"] },
        { "name": "address", "type": "text", "nullable": true },
        { "name": "created_at", "type": "timestamptz", "nullable": false, "constraints": ["DEFAULT now()"] },
        { "name": "updated_at", "type": "timestamptz", "nullable": false, "constraints": ["DEFAULT now()"] }
      ],
      "relationships": [
        { "type": "one-to-many", "target": "Equipment", "foreign_key": "equipment.location_id" },
        { "type": "one-to-many", "target": "AuditSession", "foreign_key": "audit_sessions.location_id" }
      ]
    },
    {
      "name": "User",
      "table": "users",
      "fields": [
        { "name": "id", "type": "uuid", "nullable": false, "constraints": ["PRIMARY KEY"] },
        { "name": "email", "type": "varchar(255)", "nullable": false, "constraints": ["UNIQUE"] },
        { "name": "full_name", "type": "varchar(100)", "nullable": false },
        { "name": "role", "type": "enum('director','delegate')", "nullable": false },
        { "name": "is_active", "type": "boolean", "nullable": false, "constraints": ["DEFAULT true"] },
        { "name": "password_hash", "type": "varchar(255)", "nullable": false },
        { "name": "created_at", "type": "timestamptz", "nullable": false, "constraints": ["DEFAULT now()"] },
        { "name": "updated_at", "type": "timestamptz", "nullable": false, "constraints": ["DEFAULT now()"] }
      ],
      "relationships": []
    },
    {
      "name": "Equipment",
      "table": "equipment",
      "fields": [
        { "name": "id", "type": "uuid", "nullable": false, "constraints": ["PRIMARY KEY"] },
        { "name": "name", "type": "varchar(150)", "nullable": false },
        { "name": "category", "type": "enum('laptop','desktop','printer','phone','tablet','monitor','projector','other')", "nullable": false },
        { "name": "manufacturer", "type": "varchar(100)", "nullable": true },
        { "name": "model", "type": "varchar(100)", "nullable": true },
        { "name": "serial_number", "type": "varchar(100)", "nullable": true, "constraints": ["UNIQUE WHERE NOT NULL"] },
        { "name": "qr_code", "type": "varchar(36)", "nullable": false, "constraints": ["UNIQUE"] },
        { "name": "location_id", "type": "uuid", "nullable": false, "constraints": ["FK → locations.id RESTRICT"] },
        { "name": "room", "type": "varchar(100)", "nullable": true },
        { "name": "assigned_to", "type": "varchar(100)", "nullable": true },
        { "name": "status", "type": "enum('active','retired')", "nullable": false, "constraints": ["DEFAULT 'active'"] },
        { "name": "retired_at", "type": "timestamptz", "nullable": true },
        { "name": "retired_by_id", "type": "uuid", "nullable": true, "constraints": ["FK → users.id SET NULL"] },
        { "name": "retirement_reason", "type": "text", "nullable": true },
        { "name": "created_at", "type": "timestamptz", "nullable": false, "constraints": ["DEFAULT now()"] },
        { "name": "updated_at", "type": "timestamptz", "nullable": false, "constraints": ["DEFAULT now()"] },
        { "name": "created_by_id", "type": "uuid", "nullable": false, "constraints": ["FK → users.id RESTRICT"] }
      ],
      "relationships": [
        { "type": "many-to-one", "target": "Location", "foreign_key": "location_id" },
        { "type": "many-to-one", "target": "User", "foreign_key": "created_by_id" },
        { "type": "many-to-one", "target": "User", "foreign_key": "retired_by_id" }
      ]
    },
    {
      "name": "AuditSession",
      "table": "audit_sessions",
      "fields": [
        { "name": "id", "type": "uuid", "nullable": false, "constraints": ["PRIMARY KEY"] },
        { "name": "location_id", "type": "uuid", "nullable": false, "constraints": ["FK → locations.id RESTRICT"] },
        { "name": "started_by_id", "type": "uuid", "nullable": false, "constraints": ["FK → users.id RESTRICT"] },
        { "name": "started_at", "type": "timestamptz", "nullable": false, "constraints": ["DEFAULT now()"] },
        { "name": "completed_at", "type": "timestamptz", "nullable": true },
        { "name": "status", "type": "enum('in_progress','completed')", "nullable": false, "constraints": ["DEFAULT 'in_progress'"] },
        { "name": "notes", "type": "text", "nullable": true }
      ],
      "relationships": [
        { "type": "many-to-one", "target": "Location", "foreign_key": "location_id" },
        { "type": "many-to-one", "target": "User", "foreign_key": "started_by_id" },
        { "type": "one-to-many", "target": "AuditItem", "foreign_key": "audit_items.audit_session_id" }
      ]
    },
    {
      "name": "AuditItem",
      "table": "audit_items",
      "fields": [
        { "name": "id", "type": "uuid", "nullable": false, "constraints": ["PRIMARY KEY"] },
        { "name": "audit_session_id", "type": "uuid", "nullable": false, "constraints": ["FK → audit_sessions.id CASCADE"] },
        { "name": "equipment_id", "type": "uuid", "nullable": false, "constraints": ["FK → equipment.id RESTRICT"] },
        { "name": "check_method", "type": "enum('scan','manual')", "nullable": true },
        { "name": "checked_at", "type": "timestamptz", "nullable": true },
        { "name": "is_present", "type": "boolean", "nullable": true }
      ],
      "relationships": [
        { "type": "many-to-one", "target": "AuditSession", "foreign_key": "audit_session_id" },
        { "type": "many-to-one", "target": "Equipment", "foreign_key": "equipment_id" }
      ]
    }
  ],
  "roles": [
    {
      "name": "director",
      "permissions": ["locations:read", "locations:write", "equipment:read", "equipment:write", "equipment:retire", "equipment:export", "audits:read", "audits:write", "users:read", "users:write"]
    },
    {
      "name": "delegate",
      "permissions": ["locations:read", "locations:write", "equipment:read", "equipment:write", "equipment:retire", "equipment:export", "audits:read", "audits:write"]
    }
  ],
  "endpoints": [
    { "id": "EP-001", "method": "POST", "path": "/api/v1/auth/login", "auth": "anonymous", "request_schema": "LoginRequest", "response_schema": "TokenResponse", "requirement_refs": ["R-010"] },
    { "id": "EP-002", "method": "POST", "path": "/api/v1/auth/refresh", "auth": "anonymous", "request_schema": "RefreshRequest", "response_schema": "AccessTokenResponse", "requirement_refs": ["R-010"] },
    { "id": "EP-003", "method": "POST", "path": "/api/v1/auth/logout", "auth": "required", "permission": "any", "request_schema": "RefreshRequest", "response_schema": "none", "requirement_refs": ["R-010"] },
    { "id": "EP-004", "method": "GET", "path": "/api/v1/locations", "auth": "required", "permission": "locations:read", "request_schema": "none", "response_schema": "LocationListResponse", "requirement_refs": ["R-014"] },
    { "id": "EP-005", "method": "POST", "path": "/api/v1/locations", "auth": "required", "permission": "locations:write", "request_schema": "LocationCreateRequest", "response_schema": "Location", "requirement_refs": ["R-011"] },
    { "id": "EP-006", "method": "GET", "path": "/api/v1/locations/{id}", "auth": "required", "permission": "locations:read", "request_schema": "none", "response_schema": "LocationDetail", "requirement_refs": ["R-014"] },
    { "id": "EP-007", "method": "PUT", "path": "/api/v1/locations/{id}", "auth": "required", "permission": "locations:write", "request_schema": "LocationUpdateRequest", "response_schema": "Location", "requirement_refs": ["R-011"] },
    { "id": "EP-008", "method": "DELETE", "path": "/api/v1/locations/{id}", "auth": "required", "permission": "locations:write", "request_schema": "none", "response_schema": "none", "requirement_refs": ["R-011"] },
    { "id": "EP-009", "method": "GET", "path": "/api/v1/equipment", "auth": "required", "permission": "equipment:read", "request_schema": "EquipmentListQuery", "response_schema": "EquipmentListResponse", "requirement_refs": ["R-001", "R-012"] },
    { "id": "EP-010", "method": "POST", "path": "/api/v1/equipment", "auth": "required", "permission": "equipment:write", "request_schema": "EquipmentCreateRequest", "response_schema": "Equipment", "requirement_refs": ["R-001", "R-004"] },
    { "id": "EP-011", "method": "GET", "path": "/api/v1/equipment/{id}", "auth": "required", "permission": "equipment:read", "request_schema": "none", "response_schema": "Equipment", "requirement_refs": ["R-001"] },
    { "id": "EP-012", "method": "PUT", "path": "/api/v1/equipment/{id}", "auth": "required", "permission": "equipment:write", "request_schema": "EquipmentUpdateRequest", "response_schema": "Equipment", "requirement_refs": ["R-002"] },
    { "id": "EP-013", "method": "POST", "path": "/api/v1/equipment/{id}/retire", "auth": "required", "permission": "equipment:retire", "request_schema": "RetireRequest", "response_schema": "Equipment", "requirement_refs": ["R-003"] },
    { "id": "EP-014", "method": "GET", "path": "/api/v1/equipment/{id}/qr", "auth": "required", "permission": "equipment:read", "request_schema": "none", "response_schema": "image/png", "requirement_refs": ["R-004", "R-005"] },
    { "id": "EP-015", "method": "GET", "path": "/api/v1/equipment/export", "auth": "required", "permission": "equipment:export", "request_schema": "EquipmentExportQuery", "response_schema": "application/xlsx", "requirement_refs": ["R-015", "R-016"] },
    { "id": "EP-016", "method": "POST", "path": "/api/v1/audits", "auth": "required", "permission": "audits:write", "request_schema": "AuditStartRequest", "response_schema": "AuditSessionResponse", "requirement_refs": ["R-006"] },
    { "id": "EP-017", "method": "GET", "path": "/api/v1/audits", "auth": "required", "permission": "audits:read", "request_schema": "AuditListQuery", "response_schema": "AuditListResponse", "requirement_refs": ["R-006"] },
    { "id": "EP-018", "method": "GET", "path": "/api/v1/audits/{id}", "auth": "required", "permission": "audits:read", "request_schema": "none", "response_schema": "AuditDetail", "requirement_refs": ["R-006", "R-009"] },
    { "id": "EP-019", "method": "POST", "path": "/api/v1/audits/{id}/scan", "auth": "required", "permission": "audits:write", "request_schema": "ScanRequest", "response_schema": "AuditItem", "requirement_refs": ["R-007"] },
    { "id": "EP-020", "method": "POST", "path": "/api/v1/audits/{id}/manual", "auth": "required", "permission": "audits:write", "request_schema": "ManualCheckRequest", "response_schema": "AuditItem", "requirement_refs": ["R-008"] },
    { "id": "EP-021", "method": "POST", "path": "/api/v1/audits/{id}/complete", "auth": "required", "permission": "audits:write", "request_schema": "none", "response_schema": "AuditSession", "requirement_refs": ["R-009"] },
    { "id": "EP-022", "method": "GET", "path": "/api/v1/audits/{id}/report", "auth": "required", "permission": "audits:read", "request_schema": "ReportQuery", "response_schema": "AuditReport|application/pdf", "requirement_refs": ["R-009", "R-013"] },
    { "id": "EP-023", "method": "GET", "path": "/api/v1/users", "auth": "required", "permission": "users:read", "request_schema": "none", "response_schema": "UserListResponse", "requirement_refs": ["R-011"] },
    { "id": "EP-024", "method": "POST", "path": "/api/v1/users", "auth": "required", "permission": "users:write", "request_schema": "UserCreateRequest", "response_schema": "User", "requirement_refs": ["R-011"] },
    { "id": "EP-025", "method": "PUT", "path": "/api/v1/users/{id}", "auth": "required", "permission": "users:write", "request_schema": "UserUpdateRequest", "response_schema": "User", "requirement_refs": ["R-011"] },
    { "id": "EP-026", "method": "DELETE", "path": "/api/v1/users/{id}", "auth": "required", "permission": "users:write", "request_schema": "none", "response_schema": "none", "requirement_refs": ["R-011"] }
  ],
  "ui_components": [
    { "name": "LoginPage", "page": "/login", "type": "page", "data_source": "EP-001", "auth": "anonymous" },
    { "name": "DashboardPage", "page": "/dashboard", "type": "page", "data_source": "EP-004,EP-009", "auth": "required" },
    { "name": "LocationListPage", "page": "/locations", "type": "page", "data_source": "EP-004", "auth": "required" },
    { "name": "LocationDetailPage", "page": "/locations/{id}", "type": "page", "data_source": "EP-006,EP-009", "auth": "required" },
    { "name": "EquipmentListPage", "page": "/equipment", "type": "page", "data_source": "EP-009,EP-015", "auth": "required" },
    { "name": "EquipmentDetailPage", "page": "/equipment/{id}", "type": "page", "data_source": "EP-011", "auth": "required" },
    { "name": "EquipmentCreateModal", "page": "modal", "type": "modal", "data_source": "EP-010", "auth": "required" },
    { "name": "EquipmentEditModal", "page": "modal", "type": "modal", "data_source": "EP-012", "auth": "required" },
    { "name": "QRPrintPage", "page": "/equipment/{id}/qr", "type": "page", "data_source": "EP-014", "auth": "required" },
    { "name": "AuditListPage", "page": "/audits", "type": "page", "data_source": "EP-017", "auth": "required" },
    { "name": "AuditSessionPage", "page": "/audits/{id}", "type": "page", "data_source": "EP-018,EP-019,EP-020,EP-021", "auth": "required" },
    { "name": "AuditReportPage", "page": "/audits/{id}/report", "type": "page", "data_source": "EP-022", "auth": "required" },
    { "name": "UserManagementPage", "page": "/users", "type": "page", "data_source": "EP-023,EP-024,EP-025,EP-026", "auth": "required" }
  ],
  "requirements": [
    { "id": "R-001", "text": "A rendszernek MUST lehetővé tennie eszköz felvételét kötelező mezőkkel (név, kategória, telephely) és opcionálisokkal (gyártó, modell, sorozatszám, szoba, felelős).", "priority": "MUST" },
    { "id": "R-002", "text": "A rendszernek MUST lehetővé tennie eszköz bármely szerkeszthető mezőjének módosítását.", "priority": "MUST" },
    { "id": "R-003", "text": "A rendszernek MUST lehetővé tennie eszköz soft-delete selejtezését okkal, visszakereshető előzményekkel.", "priority": "MUST" },
    { "id": "R-004", "text": "Eszköz létrehozásakor a rendszernek MUST automatikusan QR-kódot generálnia (halo-inv://{uuid} séma).", "priority": "MUST" },
    { "id": "R-005", "text": "A rendszernek MUST lehetővé tennie QR-kód PNG exportját nyomtatáshoz, eszköz adataival.", "priority": "MUST" },
    { "id": "R-006", "text": "A rendszernek MUST lehetővé tennie audit session indítását egy telephelyhez, automatikus item-listával.", "priority": "MUST" },
    { "id": "R-007", "text": "Aktív audit session során a rendszernek MUST lehetővé tennie eszköz QR-kód scanneléssel való megjelölését.", "priority": "MUST" },
    { "id": "R-008", "text": "Aktív audit session során a rendszernek MUST lehetővé tennie eszköz kézi megjelölését QR nélkül.", "priority": "MUST" },
    { "id": "R-009", "text": "Audit lezárásakor a rendszernek MUST riportot generálnia (jelen/hiányzó/nem ellenőrzött bontásban).", "priority": "MUST" },
    { "id": "R-010", "text": "A rendszernek MUST JWT-alapú autentikációt alkalmaznia access + refresh token párral.", "priority": "MUST" },
    { "id": "R-011", "text": "A rendszernek MUST két szerepkört támogatnia: director (teljes jog + user mgmt) és delegate (teljes jog, user mgmt nélkül).", "priority": "MUST" },
    { "id": "R-012", "text": "Az eszközlistának SHOULD szűrhetőnek lennie telephely, kategória és státusz szerint.", "priority": "SHOULD" },
    { "id": "R-013", "text": "Az audit riportnak SHOULD letölthetőnek lennie JSON vagy PDF formátumban.", "priority": "SHOULD" },
    { "id": "R-014", "text": "A rendszer MAY telephely-szintű eszközösszesítő dashboardot megjeleníteni.", "priority": "MAY" },
    { "id": "R-015", "text": "Az eszközlistának SHOULD exportálhatónak lennie Excel (.xlsx) formátumban az aktuális szűrőkkel.", "priority": "SHOULD" },
    { "id": "R-016", "text": "A selejtezett eszközöknek SHOULD exportálhatónak lenniük külön Excel fájlba számviteli célra.", "priority": "SHOULD" }
  ],
  "slices": []
}
```
