# Gami Backend

Gami is a gamification and recruitment backend built with **Django** and **Django REST Framework**.

The backend provides authentication, user management, job positions, recruitment applications, missions, points, levels, badges, and related APIs.

---

## Tech Stack

* Python
* Django
* Django REST Framework
* SQLite (development)
* JWT Authentication
* RESTful APIs

---

## Current Phase 2 Features

The current Phase 2 implementation includes the following modules:

### 1. Points & Levels

The reward system automatically manages user points and levels.

When a user completes a rewarded activity:

```text
Activity Completed
       ↓
   Award Points
       ↓
   Update Level
       ↓
 Check Badge Rules
```

Points are managed on the backend and levels are calculated based on configured point thresholds.

---

### 2. Badges

The badge system supports:

* Creating badges
* Listing available badges
* Viewing a user's badges
* Manually assigning badges
* Automatic badge assignment based on rules
* Preventing duplicate badge assignments

Currently supported automatic badge rules include mission completion based rules.

Example:

```text
Complete 3 Missions
        ↓
Automatic Badge Assignment
```

---

### 3. Missions

The mission lifecycle is managed through the backend:

```text
Assign
  ↓
Start
  ↓
Progress
  ↓
Complete
```

When a mission is completed, the backend can automatically:

* Mark the mission as completed
* Set progress to 100%
* Award points
* Recalculate the user's level
* Check automatic badge rules
* Return the earned rewards

---

### 4. Job Applications

Users can submit applications for available job positions.

The application system supports:

* Creating applications
* Viewing user's applications
* Viewing application details
* HR/Admin access to applications
* Application status management
* Application questions and answers

---

### 5. Application Questions & Answers

Job positions can have custom questions.

Users can submit answers together with their application.

The backend validates that:

* The question exists
* The question belongs to the selected job position
* The question is active
* A question is not answered more than once
* Required answer fields are provided

---

### 6. Application Status Management

The current application workflow supports the following statuses:

```text
PENDING_REVIEW
      ↓
HR_REVIEW
      ↓
WAITING_FOR_USER
      ↓
MANAGEMENT_REVIEW
      ↓
ACCEPTED
```

An application can also be marked as:

```text
REJECTED
```

HR/Admin users can update application statuses through the API.

---

## API Overview

### Authentication

JWT-based authentication is used for protected API endpoints.

### Profile

```http
GET /api/profile/
```

### Missions

```http
GET  /api/missions/
GET  /api/missions/<id>/
POST /api/missions/<id>/start/
PATCH /api/missions/<id>/progress/
POST /api/missions/<id>/complete/
```

### Mission Management

```http
POST /api/mission-management/<mission_id>/assign/
```

### Badges

```http
GET  /api/badges/
POST /api/badges/

GET  /api/badges/<id>/
GET  /api/badges/my/
GET  /api/badges/users/<user_id>/

POST /api/badges/<badge_id>/users/<user_id>/assign/
```

### Job Positions

```http
GET /api/job-positions/
GET /api/job-positions/<id>/
```

### Job Position Questions

```http
GET /api/job-positions/<job_position_id>/questions/
POST /api/questions/create/

PUT/PATCH /api/questions/<id>/
DELETE     /api/questions/<id>/
```

### Applications

```http
GET  /api/applications/
POST /api/applications/create/
GET  /api/applications/<id>/
PATCH /api/applications/<id>/status/
```

---

## Permissions

The API uses role-based access control.

Depending on the endpoint, access may be restricted to:

* Authenticated users
* Admin users
* Super Admin users

Users can access their own personal data and applications, while authorized HR/Admin users can manage recruitment-related data.

---

## Running the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/mmokht81/Gami.git
cd Gami
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Run the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

---

## Testing

The backend currently includes automated tests covering the implemented functionality.

Run the test suite with:

```bash
python manage.py test accounts
```

Current status:

```text
28 tests
28 passed
```

Django system checks can also be run with:

```bash
python manage.py check
```

---

## Project Status

### Phase 2 — Current Progress

Implemented:

* [x] Points & Rewards
* [x] Level System
* [x] Badge System
* [x] Automatic Badge Rules
* [x] Mission Lifecycle
* [x] Mission Progress
* [x] Mission Completion
* [x] Job Applications
* [x] Application Status Management
* [x] Application Questions
* [x] Application Answers
* [x] HR/Admin Application Management

Planned next:

* [ ] Onboarding
* [ ] Challenges & Competitions
* [ ] Training
* [ ] Final Integration & Improvements

---

## Development Notes

The backend is designed around service-based business logic for important operations such as missions and rewards.

For example, mission completion is handled centrally so that points, levels, and automatic badges remain consistent regardless of the client consuming the API.

The project is currently under active development as part of Phase 2.
