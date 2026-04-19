"""
core/views.py — PostgreSQL version.

Changes from MongoDB version:
  • Removed Decimal128 workarounds — PostgreSQL returns proper Python Decimal
  • Re-enabled Sum() aggregate (was disabled due to djongo Decimal128 crash)
  • Re-enabled Count(filter=Q()) (was disabled due to djongo returning wrong counts)
  • Removed d() helper import — not needed
"""
import logging
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from core.mixins import SuccessResponseMixin, success_response

logger = logging.getLogger(__name__)


class HealthCheckView(SuccessResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from rest_framework import status as drf_status
        db_ok    = True
        db_error = None
        try:
            from django.db import connection
            connection.ensure_connection()
        except Exception as exc:
            db_ok    = False
            db_error = str(exc)
        payload = {'service': 'Lakshmi Crackers API', 'database': 'ok' if db_ok else 'error'}
        if db_error:
            payload['db_error'] = db_error
        http_status = (drf_status.HTTP_200_OK if db_ok
                       else drf_status.HTTP_503_SERVICE_UNAVAILABLE)
        return success_response(payload, http_status=http_status)


class AdminDashboardStatsView(SuccessResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from products.models import Product, Category
        from orders.models   import Order, Coupon, OrderItem
        from users.models    import User

        # ── Products ─────────────────────────────────────────────────────────
        # Count(filter=Q()) now works correctly with PostgreSQL
        p_stats = Product.objects.filter(is_active=True).aggregate(
            total        = Count('id'),
            out_of_stock = Count('id', filter=Q(stock=0)),
            low_stock    = Count('id', filter=Q(stock__gt=0, stock__lte=10)),
        )

        low_stock_items = list(
            Product.objects
            .filter(is_active=True, stock__lte=10)
            .select_related('category')          # single JOIN — safe with PostgreSQL
            .order_by('stock')
            .values('id', 'name', 'stock', 'category__name')[:10]
        )
        # Normalise key name to match existing frontend contract
        for item in low_stock_items:
            item['category_name'] = item.pop('category__name') or ''

        # ── Revenue — Sum() works perfectly with PostgreSQL ───────────────────
        revenue = (
            Order.objects
            .exclude(status='cancelled')
            .aggregate(total=Sum('total'))['total']
        ) or 0

        # ── Order counts — Count(filter=Q()) works correctly with PostgreSQL ──
        o_stats = Order.objects.aggregate(
            total      = Count('id'),
            pending    = Count('id', filter=Q(status='pending')),
            confirmed  = Count('id', filter=Q(status='confirmed')),
            processing = Count('id', filter=Q(status='processing')),
            shipped    = Count('id', filter=Q(status='shipped')),
            delivered  = Count('id', filter=Q(status='delivered')),
            cancelled  = Count('id', filter=Q(status='cancelled')),
        )

        # ── Recent orders ─────────────────────────────────────────────────────
        recent_raw = list(
            Order.objects
            .annotate(items_count=Count('items'))
            .order_by('-created_at')
            .values('id', 'name', 'email', 'total', 'status', 'created_at', 'items_count')[:5]
        )
        recent_orders = [
            {
                'id':         r['id'],
                'name':       r['name'],
                'email':      r['email'],
                'total':      str(r['total']),
                'status':     r['status'],
                'item_count': r['items_count'],
                'created_at': r['created_at'].isoformat(),
            }
            for r in recent_raw
        ]

        # ── Users ─────────────────────────────────────────────────────────────
        u_stats = User.objects.aggregate(
            total     = Count('id'),
            customers = Count('id', filter=Q(is_staff=False)),
        )

        # ── Coupons ───────────────────────────────────────────────────────────
        coupon_stats = Coupon.objects.aggregate(
            total  = Count('id'),
            active = Count('id', filter=Q(is_active=True)),
        )

        return self.ok({
            'products':      {**p_stats, 'low_stock_items': low_stock_items},
            'orders':        {**o_stats, 'revenue': str(revenue)},
            'coupons':       coupon_stats,
            'users':         {**u_stats, 'total': u_stats['total']},
            'recent_orders': recent_orders,
        })
