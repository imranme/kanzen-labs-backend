from rest_framework import serializers
from .models import Meeting
 
class MeetingScheduleSerializer(serializers.ModelSerializer):
    meeting_link = serializers.ReadOnlyField(source='jitsi_meet_url')
    host_name = serializers.SerializerMethodField()
    scheduled_at = serializers.DateTimeField(source='scheduled_datetime')
    participant_emails = serializers.JSONField(source='invited_emails', required=False, default=list)
 
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'description', 'host_name',
            'scheduled_at', 'duration_minutes',
            'jitsi_room_name', 'meeting_link', 'participant_emails', 'created_at'
        ]
        read_only_fields = ['id', 'jitsi_room_name', 'created_at']
 
    def get_host_name(self, obj):
        if hasattr(obj.host, 'brand_name'):
            return obj.host.brand_name
        return str(obj.host)