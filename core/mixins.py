"""
core/mixins.py — Response helpers and pagination.
Simple PageNumberPagination with the success envelope.
PostgreSQL version — standard ORM operations.tegerField.
"""
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status


def success_response(data=None, message='', http_status=status.HTTP_200_OK):
    body = {'success': True}
    if message:
        body['message'] = message
    if data is not None:
        body['data'] = data
    return Response(body, status=http_status)


def created_response(data=None, message='Created successfully.'):
    return success_response(data, message, http_status=status.HTTP_201_CREATED)


def deleted_response(message='Deleted successfully.'):
    return Response({'success': True, 'message': message}, status=status.HTTP_200_OK)


class SuccessResponseMixin:
    def ok(self, data=None, message=''):
        return success_response(data, message)

    def created(self, data=None, message='Created successfully.'):
        return created_response(data, message)

    def deleted(self, message='Deleted successfully.'):
        return deleted_response(message)


class PaginatedResponseMixin:
    """Wraps paginated list responses in the success envelope."""

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page     = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginator  = self.paginator
            return Response({
                'success':  True,
                'count':    paginator.page.paginator.count,
                'next':     paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'data':     serializer.data,
            })

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
