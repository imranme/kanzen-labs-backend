from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from apps.users.permissions import IsApprovedPartner
from .models import Meeting, MeetingParticipant, MeetingType, MeetingStatus
from .serializers import (
    MeetingListSerializer,
    MeetingDetailSerializer,
    InstantMeetingSerializer,
    ScheduleMeetingSerializer,
)
from .services import create_hms_room, get_join_token, end_hms_room

PERMS = [IsAuthenticated, IsApprovedPartner]


class MeetingListView(APIView):
    permission_classes = PERMS

    def get(self, request):
        brand    = request.user.profile
        qs       = Meeting.objects.filter(host=brand)
        status_f = request.query_params.get("status")
        if status_f:
            qs = qs.filter(status=status_f)
        return Response(MeetingListSerializer(qs, many=True).data)


class InstantMeetingView(GenericAPIView):
    serializer_class   = InstantMeetingSerializer
    permission_classes = PERMS

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d     = serializer.validated_data
        brand = request.user.profile

        title = d.get("title", "Instant Meeting")

        room = create_hms_room(title)

        meeting = Meeting.objects.create(
            host         = brand,
            title        = title,
            meeting_type = MeetingType.INSTANT,
            status       = MeetingStatus.LIVE,
            scheduled_at = timezone.now(),
            hms_room_id  = room["room_id"],
            meeting_link = room["meeting_link"],
        )

        host_token = get_join_token(
            room_id   = meeting.hms_room_id,
            user_id   = str(request.user.id),
            user_name = brand.brand_name,
            role      = "host",
        )

        MeetingParticipant.objects.create(
            meeting    = meeting,
            email      = request.user.email,
            name       = brand.brand_name,
            is_host    = True,
            joined_at  = timezone.now(),
            join_token = host_token,
        )

        for email in d.get("participant_emails", []):
            if email != request.user.email:
                MeetingParticipant.objects.get_or_create(
                    meeting=meeting, 
                    email=email,
                    defaults={"name": email.split('@')[0]}
                )

        return Response(
            {
                "meeting":      MeetingDetailSerializer(meeting).data,
                "meeting_link": meeting.meeting_link,
                "meeting_code": meeting.meeting_code,
                "join_token":   host_token,
                "room_id":      meeting.hms_room_id,
                "message":      "Instant meeting started! Use join_token to connect via the 100ms SDK.",
            },
            status=status.HTTP_201_CREATED,
        )


class ScheduleMeetingView(GenericAPIView):
    serializer_class   = ScheduleMeetingSerializer
    permission_classes = PERMS

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d     = serializer.validated_data
        brand = request.user.profile

        room = create_hms_room(d["title"])

        meeting = Meeting.objects.create(
            host             = brand,
            title            = d["title"],
            description      = d.get("description", ""),
            meeting_type     = MeetingType.SCHEDULED,
            status           = MeetingStatus.UPCOMING,
            scheduled_at     = d["scheduled_at"],
            duration_minutes = d.get("duration_minutes", 30),
            hms_room_id      = room["room_id"],
            meeting_link     = room["meeting_link"],
        )

        MeetingParticipant.objects.create(
            meeting=meeting, email=request.user.email,
            name=brand.brand_name, is_host=True,
        )

        for email in d.get("participant_emails", []):
            if email != request.user.email:
                MeetingParticipant.objects.get_or_create(
                    meeting=meeting, 
                    email=email,
                    defaults={"name": email.split('@')[0]}
                )

        return Response(
            {
                "meeting":      MeetingDetailSerializer(meeting).data,
                "meeting_link": meeting.meeting_link,
                "meeting_code": meeting.meeting_code,
                "message":      f"Meeting scheduled! Link ready for {len(d.get('participant_emails', []))} participants.",
            },
            status=status.HTTP_201_CREATED,
        )


class MeetingDetailView(APIView):
    permission_classes = PERMS

    def _get(self, request, pk):
        try:
            return Meeting.objects.get(pk=pk, host=request.user.profile)
        except Meeting.DoesNotExist:
            return None

    def get(self, request, pk):
        meeting = self._get(request, pk)
        if not meeting:
            return Response({"error": "Meeting not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(MeetingDetailSerializer(meeting).data)

    def delete(self, request, pk):
        meeting = self._get(request, pk)
        if not meeting:
            return Response({"error": "Meeting not found."}, status=status.HTTP_404_NOT_FOUND)

        end_hms_room(meeting.hms_room_id)
        meeting.status = MeetingStatus.CANCELLED
        meeting.save(update_fields=["status"])

        return Response({"message": "Meeting cancelled."}, status=status.HTTP_200_OK)


class JoinMeetingView(APIView):
    permission_classes = PERMS

    def post(self, request, pk):
        try:
            meeting = Meeting.objects.get(pk=pk)
        except Meeting.DoesNotExist:
            return Response({"error": "Meeting not found."}, status=status.HTTP_404_NOT_FOUND)

        if meeting.status == MeetingStatus.CANCELLED:
            return Response({"error": "This meeting has been cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        is_host = (meeting.host == request.user.profile)
        role    = "host" if is_host else "guest"

        join_token = get_join_token(
            room_id   = meeting.hms_room_id,
            user_id   = str(request.user.id),
            user_name = request.user.profile.brand_name,
            role      = role,
        )

        participant, created = MeetingParticipant.objects.get_or_create(
            meeting = meeting,
            email   = request.user.email,
            defaults={
                "name":       request.user.profile.brand_name,
                "is_host":    is_host,
                "joined_at":  timezone.now(),
                "join_token": join_token,
            }
        )
        if not created:
            participant.joined_at  = timezone.now()
            participant.join_token = join_token
            participant.save(update_fields=["joined_at", "join_token"])

        if meeting.status == MeetingStatus.UPCOMING:
            meeting.status = MeetingStatus.LIVE
            meeting.save(update_fields=["status"])

        return Response({
            "meeting_link": meeting.meeting_link,
            "meeting_code": meeting.meeting_code,
            "room_id":      meeting.hms_room_id,
            "join_token":   join_token,
            "role":         role,
            "title":        meeting.title,
            "status":       meeting.status,
            "message":      "Use join_token with the 100ms SDK to connect.",
        })


class AddParticipantView(APIView):
    permission_classes = PERMS

    def post(self, request, pk):
        meeting = Meeting.objects.filter(pk=pk, host=request.user.profile).first()
        if not meeting:
            return Response({"error": "Meeting not found."}, status=status.HTTP_404_NOT_FOUND)

        email = request.data.get("email", "").strip()
        name  = request.data.get("name", "").strip() or email.split('@')[0]

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        participant, created = MeetingParticipant.objects.get_or_create(
            meeting=meeting, email=email, defaults={"name": name}
        )
        if not created:
            return Response({"message": "Participant already added."})

        return Response(
            {"message": f"{email} added to the meeting.", "meeting_link": meeting.meeting_link},
            status=status.HTTP_201_CREATED,
        )


class EndMeetingView(APIView):
    permission_classes = PERMS

    def post(self, request, pk):
        meeting = Meeting.objects.filter(pk=pk, host=request.user.profile).first()
        if not meeting:
            return Response({"error": "Meeting not found."}, status=status.HTTP_404_NOT_FOUND)

        end_hms_room(meeting.hms_room_id)
        meeting.status = MeetingStatus.COMPLETED
        meeting.save(update_fields=["status"])

        return Response({"message": "Meeting ended for all participants."})