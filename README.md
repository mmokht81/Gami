# Gami Authentication System

A Django authentication system using **One-Time Password (OTP)** with mobile number login.

### Features

* Mobile number authentication
* Secure 6-digit OTP
* OTP expiration
* Resend OTP
* Login attempt limit
* Custom User model
* Clean and scalable architecture

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Create and activate a virtual environment:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open your browser and visit:

```
http://127.0.0.1:8000/
```
