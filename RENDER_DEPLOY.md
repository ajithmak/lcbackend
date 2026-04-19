# Render Deployment Guide — Lakshmi Crackers Backend

## Root Cause of Build Failure
Render was using Python 3.14 (too new). `Pillow` and `psycopg2-binary` 
don't have pre-built wheels for Python 3.14 yet, causing the build error:
`ERROR: Failed to build 'Pillow' when getting requirements to build wheel`

## Fixes Applied
1. `runtime.txt` — pins Python to **3.11.9** (stable, all wheels available)
2. `requirements.txt` — updated `Pillow==10.4.0` (latest with 3.11 wheels), added `gunicorn` and `whitenoise`
3. `settings.py` — added WhiteNoise for static files, fixed ALLOWED_HOSTS for Render
4. `render.yaml` — Render service config
5. `Procfile` — gunicorn start command

## Step-by-Step Render Setup

### 1. Create a PostgreSQL database on Render
- Dashboard → New → PostgreSQL
- Copy the **Internal Database URL** (used inside Render)

### 2. Create a Web Service
- Dashboard → New → Web Service
- Connect your GitHub repo (or upload the code)
- Set these settings:
  - **Runtime:** Python 3
  - **Build Command:** `pip install -r requirements.txt && python manage.py migrate --no-input && python manage.py collectstatic --no-input`
  - **Start Command:** `gunicorn lakshmi_crackers.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 3. Set Environment Variables in Render Dashboard
Go to your web service → Environment → Add the following:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.9` |
| `SECRET_KEY` | (generate a random 50-char string) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `*` (or your render domain) |
| `POSTGRES_DB` | (from your Render PostgreSQL) |
| `POSTGRES_USER` | (from your Render PostgreSQL) |
| `POSTGRES_PASSWORD` | (from your Render PostgreSQL) |
| `POSTGRES_HOST` | (Internal hostname from Render PostgreSQL) |
| `POSTGRES_PORT` | `5432` |

### 4. After first deploy succeeds, seed data (optional)
Open Render Shell (your service → Shell):
```
python manage.py createsuperuser
python manage.py seed_data
```

### 5. Update frontend API URL
In your Vercel frontend, set:
```
REACT_APP_API_URL=https://your-render-service.onrender.com/api/v1
REACT_APP_BACKEND_URL=https://your-render-service.onrender.com
```

## Generate a SECRET_KEY
Run this in any Python shell:
```python
import secrets
print(secrets.token_urlsafe(50))
```
