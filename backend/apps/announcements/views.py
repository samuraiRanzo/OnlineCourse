from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdmin
from .models import Announcement, AnnouncementRead
from .serializers import AnnouncementSerializer, AnnouncementReadSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Announcement.objects.select_related('course').prefetch_related('reads')
        # Students only see announcements for enrolled courses
        if self.request.user.is_student:
            enrolled_ids = self.request.user.enrollments.values_list('course_id', flat=True)
            qs = qs.filter(course_id__in=enrolled_ids)
        # Optional filter by course
        course_id = self.request.query_params.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated],
            url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Student marks a single announcement as read."""
        announcement = self.get_object()
        obj, created = AnnouncementRead.objects.get_or_create(
            announcement=announcement,
            student=request.user,
        )
        return Response(
            AnnouncementReadSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated],
            url_path='mark-all-read')
    def mark_all_read(self, request):
        """Student marks all announcements in their enrolled courses as read."""
        enrolled_ids  = request.user.enrollments.values_list('course_id', flat=True)
        announcements = Announcement.objects.filter(course_id__in=enrolled_ids)
        created_count = 0
        for ann in announcements:
            _, created = AnnouncementRead.objects.get_or_create(
                announcement=ann, student=request.user
            )
            if created:
                created_count += 1
        return Response({'marked_read': created_count})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated],
            url_path='unread-count')
    def unread_count(self, request):
        """Returns total unread announcement count for the current student."""
        if request.user.is_admin:
            return Response({'unread': 0})
        enrolled_ids = request.user.enrollments.values_list('course_id', flat=True)
        read_ids     = AnnouncementRead.objects.filter(
            student=request.user
        ).values_list('announcement_id', flat=True)
        unread = Announcement.objects.filter(
            course_id__in=enrolled_ids
        ).exclude(id__in=read_ids).count()
        return Response({'unread': unread})
