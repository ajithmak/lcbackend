"""
orders/views.py
djongo-safe: all FK filters use _id column (user_id=, category_id=).
prefetch_related fires separate queries — never a JOIN.
search_fields only contains fields on orders_order table.
"""
import logging
from datetime import datetime
from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.db.models import prefetch_related_objects

from core.mixins import SuccessResponseMixin, PaginatedResponseMixin
from core.throttles import OrderPlacementThrottle, CouponValidateThrottle

from .models import Order, Coupon
from .serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderStatusUpdateSerializer,
    CouponSerializer,
    CouponValidateSerializer,
)

logger = logging.getLogger(__name__)


class PlaceOrderView(SuccessResponseMixin, APIView):
    """POST /api/v1/orders/place/"""
    permission_classes = [AllowAny]
    throttle_classes   = [OrderPlacementThrottle]

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        s    = OrderCreateSerializer(data=request.data, context={'user': user})
        s.is_valid(raise_exception=True)
        try:
            order = s.save()
        except IntegrityError as exc:
            logger.error('Order IntegrityError: %s', exc)
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Could not complete order due to a data conflict. Please retry.')

        logger.info('Order #%s placed by %s', order.id, order.email)
        return self.created(
            data={
                'order_id':   order.id,
                'total':      str(order.total),
                'status':     order.status,
                'created_at': order.created_at.isoformat(),
            },
            message='Order placed! Our team will contact you for payment.',
        )


class ValidateCouponView(SuccessResponseMixin, APIView):
    """POST /api/v1/orders/coupon/validate/"""
    permission_classes = [AllowAny]
    throttle_classes   = [CouponValidateThrottle]

    def post(self, request):
        s = CouponValidateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd     = s.validated_data
        coupon = vd['coupon']
        return self.ok(
            data={
                'valid':                    True,
                'code':                     coupon.code,
                'discount':                 str(vd['discount']),
                'discount_type':            coupon.discount_type,
                'discount_value':           str(coupon.discount_value),
                'min_order_value':          str(coupon.min_order_value),
                'excluded_category_slugs':  coupon.excluded_category_slugs,
            },
            message=f'Coupon applied — you save ₹{vd["discount"]:.0f}!',
        )


class MyOrdersView(PaginatedResponseMixin, generics.ListAPIView):
    """GET /api/v1/orders/my/"""
    serializer_class   = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user_id=self.request.user.id)
            .prefetch_related('items')
            .order_by('-created_at')
        )


class OrderDetailView(SuccessResponseMixin, generics.RetrieveAPIView):
    """GET /api/v1/orders/<pk>/"""
    serializer_class   = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all().prefetch_related('items')
        return Order.objects.filter(user_id=self.request.user.id).prefetch_related('items')

    def retrieve(self, request, *args, **kwargs):
        return self.ok(self.get_serializer(self.get_object()).data)


class AdminOrderListView(PaginatedResponseMixin, generics.ListAPIView):
    """GET /api/v1/orders/admin/"""
    serializer_class   = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['name', 'email', 'phone', 'coupon_code']
    ordering_fields    = ['created_at', 'total', 'status']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs = Order.objects.all().prefetch_related('items')

        status_param = self.request.query_params.get('status')
        if status_param:
            valid = [s[0] for s in Order.STATUS_CHOICES]
            if status_param not in valid:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'status': f'Invalid. Choose: {", ".join(valid)}'})
            qs = qs.filter(status=status_param)

        date_from = self.request.query_params.get('date_from')
        date_to   = self.request.query_params.get('date_to')
        if date_from:
            try:
                qs = qs.filter(created_at__gte=datetime.strptime(date_from, '%Y-%m-%d'))
            except ValueError:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'date_from': 'Use YYYY-MM-DD format.'})
        if date_to:
            try:
                qs = qs.filter(created_at__lte=datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            except ValueError:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'date_to': 'Use YYYY-MM-DD format.'})
        return qs


class AdminOrderUpdateView(SuccessResponseMixin, APIView):
    """GET/PATCH /api/v1/orders/admin/<pk>/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get(self, pk):
        order = get_object_or_404(Order, pk=pk)
        prefetch_related_objects([order], 'items')
        return order

    def get(self, request, pk):
        return self.ok(OrderDetailSerializer(self._get(pk)).data)

    def patch(self, request, pk):
        order      = self._get(pk)
        old_status = order.status
        s          = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        updated    = s.save()

        if updated.status != old_status:
            from .email import send_order_status_update
            send_order_status_update(updated)

        logger.info('Admin %s order #%s: %s→%s', request.user.email, pk, old_status, updated.status)
        return self.ok(
            data=OrderDetailSerializer(updated).data,
            message=f'Order #{pk} updated to "{updated.status}".',
        )




class AdminOrderBulkActionView(SuccessResponseMixin, APIView):
    """
    POST /api/v1/orders/admin/bulk/
    Body: { "ids": [1,2,3], "action": "delete"|"pending"|"confirmed"|"processing"|"shipped"|"delivered"|"cancelled" }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        ids    = request.data.get('ids', [])
        action = request.data.get('action', '').strip().lower()
        valid  = ('delete','pending','confirmed','processing','shipped','delivered','cancelled')

        if not ids or not isinstance(ids, list):
            return Response({'error': 'Provide a list of order IDs.'}, status=400)
        if action not in valid:
            return Response({'error': f'Unknown action "{action}".'}, status=400)

        qs    = Order.objects.filter(id__in=ids)
        count = qs.count()
        if not count:
            return Response({'error': 'No matching orders found.'}, status=404)

        if action == 'delete':
            qs.delete()
            msg = f'{count} order(s) permanently deleted.'
        else:
            qs.update(status=action)
            msg = f'{count} order(s) status updated to "{action}".'

        logger.info('Admin %s bulk %s on %d orders', request.user.email, action, count)
        return self.ok({'affected': count}, message=msg)
class AdminCouponListCreateView(SuccessResponseMixin, PaginatedResponseMixin, generics.ListCreateAPIView):
    """GET/POST /api/v1/orders/admin/coupons/"""
    serializer_class   = CouponSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset           = Coupon.objects.all().order_by('-id')

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        coupon = s.save()
        logger.info('Admin %s created coupon: %s', request.user.email, coupon.code)
        return self.created(s.data, message=f'Coupon "{coupon.code}" created.')


class AdminCouponDetailView(SuccessResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/v1/orders/admin/coupons/<pk>/"""
    serializer_class   = CouponSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset           = Coupon.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        obj     = self.get_object()
        s       = self.get_serializer(obj, data=request.data, partial=partial)
        s.is_valid(raise_exception=True)
        coupon  = s.save()
        return self.ok(s.data, message=f'Coupon "{coupon.code}" updated.')

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.used_count > 0:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f'Cannot delete coupon "{obj.code}": used {obj.used_count} time(s). Disable it instead.'
            )
        code = obj.code
        obj.delete()
        logger.info('Admin %s deleted coupon: %s', request.user.email, code)
        return self.deleted(f'Coupon "{code}" deleted.')
