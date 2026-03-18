from rest_framework import serializers
from .models import Announcement, AnnouncementRead


class AnnouncementSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    is_read      = serializers.SerializerMethodField()

    class Meta:
        model  = Announcement
        fields = [
            'id', 'course', 'course_title', 'title', 'body',
            'pinned', 'created_at', 'updated_at', 'is_read',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user.is_admin:
            return None
        return obj.reads.filter(student=request.user).exists()


class AnnouncementReadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AnnouncementRead
        fields = ['id', 'announcement', 'student', 'read_at']
        read_only_fields = ['id', 'read_at']
