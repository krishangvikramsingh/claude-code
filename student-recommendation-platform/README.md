# Student Recommendation Platform for New City Students

Software Engineering mini project — team: Krishang Vikram Singh (Roll No. B106, Batch C1), Samarendra Padaki (Roll No. B067), Riya Saitwal (Roll No. B081); B.Tech Computer Engineering,
NMIMS Mukesh Patel School of Technology Management & Engineering (Mumbai).

A web application that helps students who have moved to a new city find PGs/hostels, restaurants, stationery shops, sports
facilities and local events, using college-verified accounts, administrator-moderated ratings and reviews, filters, location
search, personalised recommendations and notifications. The requirements, UML and DFD design and test cases come from
Experiments 1–10 of the Software Engineering lab record.

**Status:** working and tested locally (96 automated tests passing, 92 % line coverage, live smoke test and browser
walkthrough recorded in `docs/evidence/`). It has **not** been hosted publicly and it does **not** use HTTPS; see
*Known limitations*.

## Quick start
```
cd student-recommendation-platform
pip install -r requirements.txt        # only needed for tests; the app itself has no dependencies
export PYTHONPATH=src
export SRP_ADMIN_PASSWORD='choose-a-strong-password'
python -m srp
```
Open http://127.0.0.1:8000/ . The first run creates `data/platform.db` and loads **sample data** (city Mumbai, college NMIMS
MPSTME with email domain `nmims.edu.in`, 10 sample listings, 3 sample events).
Sign in as the administrator with `admin@platform.in` and the password you exported. Register a student with any address
ending in `@nmims.edu.in` (the address is not checked for ownership, see below).

Run the tests: `python -m pytest -v`. Run the smoke test against a running server:
`SRP_ADMIN_PASSWORD=... python scripts/smoke_check.py`. Full instructions: `docs/06_deployment.md`.

## What it does
| Area | Implemented |
|---|---|
| Accounts | Registration with college-domain check (exact or sub-domain, case-insensitive), duplicate detection, scrypt-hashed passwords, login, logout, 5-failure / 15-minute lockout, suspended accounts refused, idle session timeout |
| Discovery | Search by category within a radius (default 5 km) sorted by distance, price/rating/distance filters, verified review counts, empty-result guidance, chronological events with type/date filters, personalised recommendations from saved preferences |
| Reviews | Integer 1–5 rating, mandatory comment, spam/profanity checks, one review per listing per student, moderation queue, approve/reject, student reports, reported reviews leave the average until resolved |
| Notifications | In-app notifications for new events, review outcomes, moderation outcomes and reports; read/unread; per-category opt-out |
| Administration | Review moderation, verify/suspend/reinstate students, add/update colleges, cities and listings, archive listings, audit log |
| Quality | SQLite persistence with constraints, role checks on the server, safe error messages, security headers, masked emails, responsive and keyboard-accessible UI |

## Layout
```
src/srp/            application (models, service rules, SQLite store, HTTP server, web UI in web/)
tests/              96 pytest tests (service, API, persistence)
scripts/            smoke_check.py, nfr_checks.py, ui_walkthrough.py, gen_test_report.py
docs/               requirements inventory, traceability, consistency analysis, NFR results, test report,
                    deployment notes, diagrams (with sources), evidence (logs, screenshots)
report/             project report (Word and PDF)
data/               SQLite database is created here (git-ignored)
```
The architecture is a small layered monolith: browser UI, HTTP/JSON interface (`server.py`), business rules (`service.py`),
and persistence (`store.py`). Working data is held in memory and every change is written through to SQLite.

## API summary
Public: `GET /health /colleges /cities /search /events /listings/{id}`, `POST /register /login`.
Signed in: `POST /logout`, `GET /me`, `PUT /me/preferences`, `GET /recommend`, `GET /notifications`,
`POST /notifications/{id}/read`, `PUT /me/notification-settings`, `POST /reviews`, `POST /reviews/{id}/report`.
Administrator: `GET /admin/reviews /admin/users /admin/audit`, `POST /reviews/{id}/validate`,
`POST /admin/users/{id}/verify|suspend|reinstate`, `POST /admin/cities /admin/colleges /admin/listings`,
`PUT|DELETE /admin/listings/{id}`. Send the token from `/login` as `Authorization: Bearer <token>`.

## Known limitations
* **No HTTPS.** Traffic is plain HTTP; put a TLS proxy in front before any public use.
* **Verification is by email domain only.** The platform does not send a confirmation email, so it cannot prove that the
  student owns the mailbox. An administrator can also verify students manually. College-ID verification is not built.
* Reviews are published after administrator approval, not within one minute (see C-01 in the consistency analysis).
* "Edit-flag" moderation, slot booking, menu/inventory updates and other Experiment 5 operations without user stories are
  not implemented.
* Notifications are in-app only. Locations are sample coordinates; there is no map or third-party data.
* Sessions are in memory (lost on restart). One process; no replication, backup job or archival job.
* Availability (99.5 %) and long-term retention could not be verified locally. Portability and accessibility were checked in
  Chromium with an automated scanner only. Login bursts of 20 simultaneous requests exceeded the 1-second target.
  Details and numbers: `docs/04_nfr_verification.md`.
* The Experiment 3 use-case image and the official mini-project guideline were not available when this was built; the
  use-case diagram was redrawn from Experiments 1, 4 and 5 (`docs/03_consistency_analysis.md`, C-14, C-15).

## Demonstration guide
1. Start the server; show the home page and search PG/Hostel (distance-sorted, cost, rating, review count).
2. Search from far away coordinates to show the "expand the radius" message; apply price and rating filters.
3. Register `name@nmims.edu.in`; try `name@gmail.com` and `name@notnmims.edu.in` to show rejection (US2, defect D-1).
4. Open a listing, submit a review, show that the rating does not change yet.
5. Log in as the administrator, approve the review, return to search: the rating and review count have changed (TC-04).
6. Report a review, show the admin queue, notifications and the audit log.
7. Show the Events tab filters, preferences on "For you", and the failed-login lockout (5 wrong passwords).
8. Run `python -m pytest -v` and `scripts/smoke_check.py`; show `docs/evidence/` and the traceability matrix.
