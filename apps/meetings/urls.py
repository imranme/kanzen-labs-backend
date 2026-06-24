from django.urls import path
from .views import (
    MeetingListView,
    MeetingScheduleView,
    InstantMeetingView,
    JoinMeetingView,
    EndMeetingView,
)
 
urlpatterns = [
    path("", MeetingListView.as_view(), name="meeting-list"),
    path("schedule/", MeetingScheduleView.as_view(), name="meeting-schedule"),
    path("instant/", InstantMeetingView.as_view(), name="meeting-instant"),
    path("<uuid:id>/join/", JoinMeetingView.as_view(), name="meeting-join"),
    path("<uuid:id>/end/", EndMeetingView.as_view(), name="meeting-end"),
]