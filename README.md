# Gami

A gamification-based recruitment platform built with **Django** and **Django REST Framework**.

## Features

* Phone number authentication
* OTP verification
* User profile management
* Mission management
* Leaderboard
* Job positions
* Job applications
* Application questions
* Application answers
* Dashboard API
* OpenAPI/Swagger documentation
* JWT Authentication

## Tech Stack

* Python
* Django
* Django REST Framework
* SQLite
* JWT (Simple JWT)
* drf-spectacular

## Installation

Clone the repository:

```bash
git clone https://github.com/mmokht81/Gami.git
cd Gami
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Create a superuser (optional):

```bash
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver
```

---

## API Documentation

Swagger UI:

```
/api/docs/
```

OpenAPI Schema:

```
/api/schema/
```

---

## Authentication

The project uses **JWT Authentication**.

Obtain an access token:

```
POST /api/token/
```

Refresh token:

```
POST /api/token/refresh/
```

Use the access token in requests:

```
Authorization: Bearer <access_token>
```

---

## Main APIs

* Authentication
* Profile
* Missions
* Leaderboard
* Dashboard
* Job Positions
* Job Applications
* Questions
* Answers

---

## Project Structure

```
accounts/
    models.py
    serializers.py
    urls.py
    views/
        auth.py
        auth_api.py
        profile.py
        leaderboard.py
        mission.py
        dashboard.py
        job_position.py
        job_application.py
        application_answer.py

Gami/
manage.py
requirements.txt
```

---

## License

This project was developed for educational and recruitment platform purposes.
