from rest_framework import serializers
from .models import Meeting, MeetingParticipant


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MeetingParticipant
        fields = ["id", "email", "name", "is_host", "joined_at"]


class MeetingListSerializer(serializers.ModelSerializer):
    host_name          = serializers.CharField(source="host.brand_name", read_only=True)
    participant_count  = serializers.IntegerField(read_only=True)
    status_label       = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model  = Meeting
        fields = [
            "id", "title", "meeting_type", "status", "status_label",
            "host_name", "participant_count",
            "scheduled_at", "duration_minutes",
            "meeting_code", "meeting_link",
            "created_at",
        ]


class MeetingDetailSerializer(serializers.ModelSerializer):
    host_name    = serializers.CharField(source="host.brand_name", read_only=True)
    participants = ParticipantSerializer(many=True, read_only=True)

    class Meta:
        model  = Meeting
        fields = [
            "id", "title", "description",
            "meeting_type", "status",
            "host_name", "participants",
            "scheduled_at", "duration_minutes",
            "meeting_code", "meeting_link", "hms_room_id",
            "created_at", "updated_at",
        ]


class InstantMeetingSerializer(serializers.Serializer):
    title               = serializers.CharField(max_length=255, required=False, default="Instant Meeting")
    participant_emails  = serializers.ListField(child=serializers.EmailField(), required=False, default=list)


class ScheduleMeetingSerializer(serializers.Serializer):
    title               = serializers.CharField(max_length=255)
    scheduled_at        = serializers.DateTimeField()
    duration_minutes    = serializers.IntegerField(default=30, min_value=5, max_value=480)
    description         = serializers.CharField(required=False, allow_blank=True, default="")
    participant_emails  = serializers.ListField(child=serializers.EmailField(), required=False, default=list)

    def validate_scheduled_at(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value