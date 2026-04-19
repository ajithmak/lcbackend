# 🔧 Backend Improvement Changelog
## Lakshmi Crackers — v1 → v2

---

## Overview

Every layer of the Django backend has been hardened:
validation is centralised, errors are consistently shaped,
DB writes are race-safe, and sensitive endpoints are throttled.

---

## 🆕 New Files Added

### `core/exceptions.py` — Centralised Error Handling
| Class / Function | Purpose |
|---|---|
| `custom_exception_handler` | Replaces DRF's default handler. Every error — validation, 404, 401, 500 — is wrapped in `{ success, error: { code, message, detail } }` |
| `ProductOutOfStock` | 409 Conflict — carries `product_name` + `available_stock` in `detail` |
| `ProductNotFound` | 404 — clean message instead of DRF's bare "Not found." |
| `CouponExpired` | 422 — distinct from "invalid code" |
| `CouponUsageLimitReached` | 422 — coupon has hit `max_uses` |
| `CouponMinOrderNotMet` | 422 — carries `min_order_value` in `detail` |
| `InvalidOrderStatus` | 400 — carries `current_status` + `requested_status` |
| `AuthenticationFailed` | 401 with machine-readable code |
| `PermissionDenied` | 403 with machine-readable code |

**Before (v1):**
```json
{ "detail": "Not found." }
```
**After (v2):**
```json
{
  "success": false,
  "error": {
    "code":    "PRODUCT_NOT_FOUND",
    "message": "No product found with slug \"gold-sparklers\"."
  }
}
```

---

### `core/validators.py` — Reusable Field Validators
All validators live in one place and are imported by every app's serializer.

| Validator | Rule |
|---|---|
| `validate_indian_phone` | Accepts 10-digit numbers starting with 6–9, strips country code & spaces, normalises to bare 10-digit |
| `validate_strong_password` | ≥8 chars, ≥1 uppercase, ≥1 digit |
| `validate_positive_price` | `Decimal > 0`, max ₹9,99,999 |
| `validate_non_negative` | For stock, min_order — rejects negatives and non-integers |
| `validate_coupon_code` | 3–20 alphanumeric + underscore, uppercased |
| `validate_address` | Minimum 10 characters |
| `validate_original_price_vs_price` | `original_price` must strictly exceed `price` |
| `validate_discount_value` | Percentage ≤100%, both types must be >0 |
| `validate_order_items` | Structural + business two-pass; rejects duplicates, >1000 qty, >50 items |

---

### `core/mixins.py` — Consistent Response Envelope
```python
# Every successful response is now:
{ "success": true, "data": { ... }, "message": "Human message." }

# Every paginated list:
{ "success": true, "count": 142, "next": "...", "previous": null, "data": [...] }
```
`SuccessResponseMixin` → `self.ok()`, `self.created()`, `self.deleted()`
`PaginatedResponseMixin` → overrides `list()` automatically

---

### `core/throttles.py` — Rate Limiting
| Throttle Class | Scope | Applied To |
|---|---|---|
| `LoginRateThrottle` | `login` → 10/min per IP | `LoginView` |
| `OrderPlacementThrottle` | `order_place` → 20/hr per IP | `PlaceOrderView` |
| `CouponValidateThrottle` | `coupon_validate` → 30/hr per IP | `ValidateCouponView` |

---

### `orders/email.py` — Email Service Module
Extracted from `views.py` into a dedicated module.
- `send_order_confirmation(order)` — Plain-text **+ HTML** email with itemised receipt table, delivery address, payment instructions
- `send_order_status_update(order)` — Triggered automatically when admin changes order status
- Both functions catch and log errors silently — email failure never crashes a request

---

### `tests/test_validation.py` — 40+ Unit & Integration Tests
| Test Class | Coverage |
|---|---|
| `PhoneValidatorTests` | 11 cases — formats, country codes, invalid starters |
| `PasswordValidatorTests` | 6 cases — length, uppercase, digit rules |
| `PriceValidatorTests` | 5 cases — zero, negative, max exceeded |
| `StockValidatorTests` | 5 cases — zero ok, string parsing, negative |
| `CouponCodeValidatorTests` | 6 cases — length, special chars, underscore |
| `AddressValidatorTests` | 3 cases — min length |
| `OriginalPriceValidatorTests` | 4 cases — gt/eq/lt/None |
| `DomainExceptionTests` | 5 cases — shape, status code, detail dict |
| `UserRegistrationAPITests` | 5 integration cases — success, duplicate, mismatch, weak pw, bad phone |
| `CouponValidationAPITests` | 5 integration cases — valid, bad code, min order, inactive, exhausted |
| `OrderStatusTransitionTests` | 2 integration cases — terminal state guard |

---

## ✏️ Modified Files

### `users/serializers.py`
| Change | Detail |
|---|---|
| Email uniqueness | Case-insensitive check on registration: `filter(email__iexact=...)` |
| Strong password | `validate_strong_password()` → min 8, uppercase, digit |
| Django validators | Also runs `django.contrib.auth.password_validation.validate_password()` (common password list) |
| Phone normalisation | `validate_indian_phone()` — returns bare 10-digit string |
| Password2 cleanup | Pops `password2` before calling `create_user()` — no stray kwarg |
| `ChangePasswordSerializer` | New: verifies current password, rejects same-as-old, runs Django validators |
| `AdminUserSerializer` | New: adds `order_count` computed field for admin user listing |

### `users/views.py`
| Change | Detail |
|---|---|
| `raise_exception=True` | All serializers — centralised error handling |
| `SuccessResponseMixin` | All responses wrapped in `{ success, data, message }` |
| `LoginRateThrottle` | Applied to `LoginView` — 10 attempts/minute |
| `ChangePasswordView` | New endpoint at `PATCH /api/v1/users/password/change/` |
| `AdminUserListView` | Now uses `IsAdminUser` permission class (was a manual `is_staff` check) |
| Logging | Every login, register, password change is logged at INFO level |

### `products/serializers.py`
| Change | Detail |
|---|---|
| Slug generation | Moved from view into `create()` / `update()` with `_generate_unique_slug()` — handles collisions with counter |
| `validate_name` | Uses `validate_product_name()` — min 3 chars, must contain letters |
| `validate_price` | Uses `validate_positive_price()` — Decimal, max ₹9,99,999 |
| `validate_original_price` | Cross-field check: must exceed `price` if provided |
| `validate_image_url` | Must start with `http://` or `https://` |
| `validate_tags` | Strips whitespace, deduplicates, lowercases, comma-joins |
| `validate` (cross-field) | `min_order ≤ stock`, `category.is_active` check |
| Category in serializer | `create()` / `update()` auto-generate slug from name; uniqueness validated |
| `StockUpdateSerializer` | Separate serializer replacing manual `int()` parsing in view |

### `products/views.py`
| Change | Detail |
|---|---|
| `_parse_price_param()` | Helper validates `min_price`/`max_price` params — bad input → 400 |
| Cross-range check | `min_price > max_price` → clear error instead of empty result |
| Soft-delete | `DELETE` on admin product sets `is_active=False` — preserves order history |
| Category delete guard | Blocks deletion if active products are assigned |
| `PaginatedResponseMixin` | All list views use standard paginated envelope |
| `SuccessResponseMixin` | All views return `{ success, data, message }` |
| Logging | All create/update/delete operations logged with admin email |

### `orders/serializers.py`
| Change | Detail |
|---|---|
| `OrderItemInputSerializer` | Dedicated per-item serializer instead of raw dict parsing |
| Two-pass item validation | Pass 1: types/structure via serializer. Pass 2: product exists, active, stock |
| Duplicate product check | `seen_ids` set rejects same product_id appearing twice in cart |
| `F()` stock deduction | `Product.objects.filter(pk=...).update(stock=F('stock') - quantity)` — race-safe atomic update |
| Coupon `F()` increment | `Coupon.objects.filter(pk=...).update(used_count=F('used_count') + 1)` — atomic |
| Coupon cross-field | Full validation in `validate()` with granular domain exceptions |
| `_subtotal/_coupon/_discount` | Stashed in `attrs` during `validate()`, consumed in `create()` — no double-calculation |
| `OrderStatusUpdateSerializer` | Validates against `_VALID_TRANSITIONS` dict — raises `InvalidOrderStatus` on bad jump |
| Status transition matrix | `pending→confirmed→processing→shipped→delivered` (one-way), `cancelled` is terminal |

### `orders/views.py`
| Change | Detail |
|---|---|
| `OrderPlacementThrottle` | 20 orders/hour per IP on `PlaceOrderView` |
| `CouponValidateThrottle` | 30 validations/hour per IP on `ValidateCouponView` |
| `IntegrityError` catch | `PlaceOrderView` catches DB integrity errors → clean 400 (not 500) |
| Status-change email | `AdminOrderUpdateView.patch()` calls `send_order_status_update()` when status changes |
| Date range filter | `AdminOrderListView` supports `?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` |
| Status filter validation | Invalid status value → 400 with list of valid options |
| Coupon delete guard | Blocks deletion of used coupons — suggests disabling instead |
| Logging | All admin actions (create/update/delete) logged with admin email + IDs |

### `lakshmi_crackers/settings.py`
| Change | Detail |
|---|---|
| `EXCEPTION_HANDLER` | `'core.exceptions.custom_exception_handler'` — wires in global error shaping |
| `DEFAULT_THROTTLE_CLASSES` | Anon + User rate limiting enabled by default |
| `DEFAULT_THROTTLE_RATES` | 5 scopes defined |
| `AUTH_PASSWORD_VALIDATORS` | Django's built-in validators enabled (similarity, length, common, numeric) |
| `LOGGING` | Structured logging config for all 4 apps + Django request logger |

---

## 📐 Consistent Error Response Format

All errors — from any endpoint — now return:
```json
{
  "success": false,
  "error": {
    "code":    "MACHINE_READABLE_CODE",
    "message": "Human-readable explanation.",
    "detail":  { "field_name": "specific error" }
  }
}
```

### Error Codes Reference
| Code | HTTP Status | Trigger |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Field validation failure |
| `NOT_AUTHENTICATED` | 401 | Missing/expired token |
| `AUTHENTICATION_FAILED` | 401 | Wrong credentials |
| `PERMISSION_DENIED` | 403 | Insufficient role |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `PRODUCT_NOT_FOUND` | 404 | Product slug not found |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP verb |
| `COUPON_INVALID` | 422 | Generic coupon error |
| `COUPON_EXPIRED` | 422 | Past `valid_until` date |
| `COUPON_LIMIT_REACHED` | 422 | `used_count >= max_uses` |
| `COUPON_MIN_ORDER` | 422 | Cart below `min_order_value` |
| `PRODUCT_OUT_OF_STOCK` | 409 | Requested qty > available stock |
| `INVALID_ORDER_STATUS` | 400 | Illegal status transition |
| `RATE_LIMIT_EXCEEDED` | 429 | Throttle exceeded |
| `INTERNAL_SERVER_ERROR` | 500 | Unhandled exception |

---

## 🏃 Running Tests

```bash
cd lakshmi_crackers_backend
source venv/bin/activate

# Run all tests
python manage.py test tests

# With coverage report
pip install coverage
coverage run manage.py test tests
coverage report -m

# Run a specific test class
python manage.py test tests.test_validation.CouponValidationAPITests
```

---

## 🆕 New API Endpoint

| Method | Path | Description |
|---|---|---|
| `PATCH` | `/api/v1/users/password/change/` | Change own password (requires `current_password`, `new_password`, `confirm_new_password`) |
