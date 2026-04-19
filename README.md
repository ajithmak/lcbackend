# Lakshmi Crackers — Backend API

Django 4.2 + Django REST Framework + MongoDB (djongo) backend.

## Quick Start

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env: set SECRET_KEY, MONGO_URI, MONGO_DB_NAME

# 4. Start MongoDB
mongod                          # or: brew services start mongodb-community

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Create admin user
python manage.py createsuperuser

# 7. Seed sample data (categories, products, coupons)
python manage.py seed_data

# 8. Start development server
python manage.py runserver
# API available at http://localhost:8000/api/v1/
```

## API Reference

### Auth (`/api/v1/users/`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/register/` | Public | Create account |
| POST | `/login/` | Public | Get JWT tokens |
| POST | `/token/refresh/` | Public | Refresh access token |
| GET/PATCH | `/profile/` | Auth | View/update profile |
| PATCH | `/password/change/` | Auth | Change password |

### Products (`/api/v1/products/`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/` | Public | List with filters |
| GET | `/featured/` | Public | Featured products |
| GET | `/categories/` | Public | All categories |
| GET | `/<slug>/` | Public | Product detail |
| GET/POST | `/admin/` | Admin | List/create products |
| GET/PATCH/DELETE | `/admin/<pk>/` | Admin | Product CRUD |
| PATCH | `/admin/<pk>/stock/` | Admin | Update stock |
| GET/POST | `/admin/categories/` | Admin | Category management |

### Orders (`/api/v1/orders/`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/place/` | Public | Place order |
| POST | `/coupon/validate/` | Public | Validate coupon |
| GET | `/my/` | Auth | My orders |
| GET | `/<pk>/` | Auth | Order detail |
| GET | `/admin/` | Admin | All orders |
| PATCH | `/admin/<pk>/` | Admin | Update status |
| GET/POST | `/admin/coupons/` | Admin | Coupon management |

## Response Format

All responses use a standard envelope:

**Success:**
```json
{ "success": true, "data": {...}, "message": "..." }
```

**Paginated:**
```json
{ "success": true, "count": 50, "next": "...", "previous": null, "data": [...] }
```

**Error:**
```json
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "detail": {...} } }
```

## Running Tests

```bash
python manage.py test tests
coverage run manage.py test tests && coverage report -m
```

## Error Codes

| Code | HTTP | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Field validation failed |
| `NOT_AUTHENTICATED` | 401 | No/expired token |
| `PERMISSION_DENIED` | 403 | Not authorised |
| `NOT_FOUND` / `PRODUCT_NOT_FOUND` | 404 | Resource missing |
| `PRODUCT_OUT_OF_STOCK` | 409 | Insufficient stock |
| `COUPON_EXPIRED` | 422 | Coupon past expiry |
| `COUPON_LIMIT_REACHED` | 422 | Coupon exhausted |
| `COUPON_MIN_ORDER` | 422 | Cart below minimum |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |
