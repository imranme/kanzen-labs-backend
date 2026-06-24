from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
 
from .models import Meeting
from .serializers import MeetingScheduleSerializer
 
class MeetingListView(ListAPIView):
    serializer_class = MeetingScheduleSerializer
    permission_classes = [IsAuthenticated]
 
    def get_queryset(self):
        user_profile = self.request.user.profile
        user_email = self.request.user.email
       
        # Return all active meetings where user is host or invited
        return Meeting.objects.filter(
            Q(host=user_profile) | Q(invited_emails__contains=user_email),
            is_cancelled=False
        ).order_by('scheduled_datetime')
 
 
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
 
 
class InstantMeetingView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request, *args, **kwargs):
        user_profile = request.user.profile
        title = request.data.get('title', 'Instant Meeting')
        participant_emails = request.data.get('participant_emails', [])
 
        meeting = Meeting.objects.create(
            title=title,
            description="",
            host=user_profile,
            scheduled_datetime=timezone.now(),
            duration_minutes=30,
            invited_emails=participant_emails
        )
 
        serializer = MeetingScheduleSerializer(meeting)
        return Response({
            "meeting": serializer.data,
            "meeting_link": meeting.jitsi_meet_url
        }, status=status.HTTP_201_CREATED)
 
 
class JoinMeetingView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request, id, *args, **kwargs):
        try:
            meeting = Meeting.objects.get(id=id, is_cancelled=False)
            return Response({
                "status": "success",
                "room_name": meeting.jitsi_room_name,
                "meeting_link": meeting.jitsi_meet_url
            }, status=status.HTTP_200_OK)
        except Meeting.DoesNotExist:
            return Response({"detail": "Meeting not found."}, status=status.HTTP_404_NOT_FOUND)
 
 
class EndMeetingView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request, id, *args, **kwargs):
        try:
            meeting = Meeting.objects.get(id=id)
            if meeting.host == request.user.profile:
                meeting.is_cancelled = True
                meeting.save()
                return Response({"status": "meeting_ended"}, status=status.HTTP_200_OK)
            return Response({"status": "left_meeting"}, status=status.HTTP_200_OK)
        except Meeting.DoesNotExist:
            return Response({"detail": "Meeting not found."}, status=status.HTTP_404_NOT_FOUND)

class MeetingListView(ListAPIView):
    serializer_class = MeetingScheduleSerializer
    permission_classes = [IsAuthenticated]
 
    def get_queryset(self):
        user_profile = self.request.user.profile
        user_email = self.request.user.email
        
       
        return Meeting.objects.filter(
            Q(host=user_profile) | Q(invited_emails__string__icontains=user_email),
            is_cancelled=False
        ).order_by('scheduled_datetime')
 