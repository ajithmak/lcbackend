# PostgreSQL Migration Guide — Lakshmi Crackers Backend

## What Changed

| Area | Before (MongoDB) | After (PostgreSQL) |
|------|-----------------|-------------------|
| Django version | 3.2.25 | 4.2.11 LTS |
| DB Engine | djongo (MongoDB) | psycopg2-binary |
| BooleanField | SmallIntegerField(0/1) workaround | Native BooleanField |
| Decimal fields | Decimal128 + d() helper | Native Python Decimal |
| Sum() aggregate | Broken (Decimal128 crash) | Works natively |
| Count(filter=Q()) | Broken (returns wrong counts) | Works natively |
| Cross-table joins | Forbidden (djongo crash) | Works natively (select_related) |
| F() expressions | Broken (djongo crash) | Works natively |
| `d()` helper | Required everywhere | Removed entirely |
| update_fields workarounds | Required for every save | Removed entirely |

## Step-by-Step Setup

### 1. Create PostgreSQL database

```sql
-- In psql or pgAdmin:
CREATE DATABASE lakshmi_crackers_db;
-- Or with a dedicated user:
CREATE USER lc_user WITH PASSWORD 'your_password';
CREATE DATABASE lakshmi_crackers_db OWNER lc_user;
GRANT ALL PRIVILEGES ON DATABASE lakshmi_crackers_db TO lc_user;
```

### 2. Configure environment

```cmd
copy .env.example .env
```

Edit `.env`:
```
POSTGRES_DB=lakshmi_crackers_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 3. Install dependencies

```cmd
python -m venv venv
venv\Scripts\activate        # Windows
# OR: source venv/bin/activate  (Linux/Mac)

pip install -r requirements.txt
```

### 4. Run migrations

```cmd
python manage.py migrate
```

This creates all tables and indexes in PostgreSQL automatically.

### 5. Create superuser

```cmd
python manage.py createsuperuser
```

### 6. Seed initial data

```cmd
python manage.py seed_data
```

### 7. Verify indexes

```cmd
python manage.py ensure_indexes
```

### 8. Run the server

```cmd
python manage.py runserver
```

## Schema Overview

```
users_user           ← Custom user (email login, BooleanField is_staff/is_active)
products_category    ← Product categories (slug, is_active)
products_product     ← Products (FK→category, BooleanField, DecimalField)
orders_coupon        ← Discount coupons (percent/fixed, validity)
orders_order         ← Customer orders (FK→user, FK→coupon)
orders_orderitem     ← Line items (FK→order, FK→product)
```

## Key Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| products_product | idx_product_active_date | Main product listing |
| products_product | idx_product_featured | Featured products widget |
| products_product | idx_product_category_active | Category filter |
| products_product | idx_product_price | Price range filter |
| orders_order | idx_order_status_date | Order management by status |
| orders_order | idx_order_email | Customer order lookup |

## Removed Files / Commands

- `ensure_indexes.py` — was MongoDB-specific; now shows PostgreSQL index status
- `d()` helper function — was needed for Decimal128→Decimal conversion; removed
- All `update_fields=[...]` workarounds in serializers — removed
- All `SmallIntegerField` boolean workarounds — converted to `BooleanField`
