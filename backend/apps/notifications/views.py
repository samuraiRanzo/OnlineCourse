from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notifications are created by signals — no POST endpoint.

    Endpoints
    ---------
    GET  /api/notifications/              — paginated list (newest first)
    GET  /api/notifications/unread-count/ — { unread: N }
    POST /api/notifications/{id}/mark-read/     — mark one as read
    POST /api/notifications/mark-all-read/      — mark all as read
    """
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Each user only sees their own notifications."""
        return Notification.objects.filter(recipient=self.request.user)

    # ── Unread count — polled by the frontend every 30s ───────────────────────

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({'unread': count})

    # ── Mark a single notification as read ────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        if not notif.is_read:
            notif.is_read = True
            notif.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notif).data)

    # ── Bulk mark-all as read ─────────────────────────────────────────────────

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({'marked_read': updated})
