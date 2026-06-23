from django.urls import path
from .views import MeetingScheduleView, UpcomingMeetingsListView

urlpatterns = [
    path("schedule/", MeetingScheduleView.as_view(), name="meeting-schedule"),
    path("upcoming/", UpcomingMeetingsListView.as_view(), name="meeting-upcoming"),
]