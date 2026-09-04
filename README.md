# Gami Backend

Gami is a gamification and recruitment backend built with **Django** and **Django REST Framework**.

The project provides authentication, recruitment, gamification, onboarding, challenges, and training features through RESTful APIs.

---

## Tech Stack

* Python
* Django
* Django REST Framework
* SQLite
* JWT Authentication
* REST APIs

---

## Features

### Authentication & Users

* Phone number registration and login
* OTP verification
* JWT authentication
* User profiles
* Role-based permissions

### Recruitment

* Job positions
* Job applications
* Application status management
* Application questions and answers
* HR/Admin application management

### Gamification

* Missions
* Mission progress and completion
* Points and levels
* Badges
* Automatic rewards
* Automatic missions

### Onboarding

* User onboarding
* Onboarding checklist
* HR progress
* Team assignment
* Completion tracking

### Challenges

* Challenges and competitions
* User participation
* Winners
* Challenge status management

### Training

* Training courses
* User enrollment
* Training sections
* Progress tracking
* Training completion
* Training rewards

---

## API Examples

### Profile

```http
GET /api/profile/
```

### Missions

```http
GET  /api/missions/
POST /api/missions/<id>/start/
PATCH /api/missions/<id>/progress/
POST /api/missions/<id>/complete/
```

### Badges

```http
GET /api/badges/
GET /api/badges/my/
```

### Applications

```http
GET  /api/applications/
POST /api/applications/create/
GET  /api/applications/<id>/
PATCH /api/applications/<id>/status/
```

### Job Positions

```http
GET /api/job-positions/
GET /api/job-positions/<id>/
```

---

## Permissions

The API uses role-based access control.

Available roles:

* `USER`
* `ADMIN`
* `SUPERADMIN`

Protected endpoints require authentication, while administrative operations require the appropriate role.

---

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/mmokht81/Gami.git
cd Gami
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Run the server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

---

## Testing

Run the test suite:

```bash
python manage.py test accounts
```

Current status:

```text
109 tests
109 passed
0 failed
```

---

## Project Status

**Phase 2 completed.**

Implemented modules:

* Authentication & Users
* Job Positions
* Job Applications
* Missions
* Points & Levels
* Badges
* Onboarding
* Challenges & Competitions
* Training
* Rewards & Idempotency

The project is ready for final integration and further development.
