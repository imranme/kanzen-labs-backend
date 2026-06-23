from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail

from .models import Meeting
from .serializers import MeetingScheduleSerializer

class MeetingScheduleView(CreateAPIView):
   
    serializer_class = MeetingScheduleSerializer
    permission_classes = [IsAuthenticated] 

    def perform_create(self, serializer):
      
        meeting = serializer.save(host=self.request.user.profile)
        
        if meeting.invited_emails:
            try:
                send_mail(
                    subject=f"Invitation: {meeting.title}",
                    message=f"You have been invited to a video call.\n\nJoin Link: {meeting.jitsi_meet_url}\nTime: {meeting.scheduled_datetime}",
                    from_email='noreply@kanzenlabs.com',
                    recipient_list=meeting.invited_emails,
                    fail_silently=True,
                )
            except Exception:
                pass


class UpcomingMeetingsListView(ListAPIView):
    
    serializer_class = MeetingScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile = self.request.user.profile
        user_email = self.request.user.email
        now = timezone.now()

        return Meeting.objects.filter(
            Q(host=user_profile) | Q(invited_emails__contains=user_email),
            scheduled_datetime__gte=now,
            is_cancelled=False
        ).order_with_respect_to('scheduled_datetime')