from django.urls import path
from .views import (
    MeetingListView,
    InstantMeetingView,
    ScheduleMeetingView,
    MeetingDetailView,
    JoinMeetingView,
    AddParticipantView,
    EndMeetingView,
)

urlpatterns = [
    path("",                        MeetingListView.as_view(),      name="meeting-list"),
    path("instant/",                InstantMeetingView.as_view(),   name="meeting-instant"),
    path("schedule/",               ScheduleMeetingView.as_view(),  name="meeting-schedule"),
    path("<uuid:pk>/",              MeetingDetailView.as_view(),    name="meeting-detail"),
    path("<uuid:pk>/join/",         JoinMeetingView.as_view(),      name="meeting-join"),
    path("<uuid:pk>/end/",          EndMeetingView.as_view(),       name="meeting-end"),
    path("<uuid:pk>/participants/", AddParticipantView.as_view(),   name="meeting-participants"),
]