import uuid
import re
from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Meeting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    host = models.ForeignKey(
        'users.PartnerProfile', 
        on_delete=models.CASCADE,
        related_name="hosted_meetings"
    )
    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    jitsi_room_name = models.CharField(max_length=150, unique=True, blank=True)
    invited_emails = models.JSONField(default=list, blank=True)
    
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meetings_meeting"
        ordering = ["scheduled_datetime"]

    def __str__(self):
        return f"{self.title} ({self.scheduled_datetime})"

    @property
    def jitsi_meet_url(self):
        jitsi_domain = getattr(settings, "JITSI_MEET_DOMAIN", "meet.ffmuc.net")
        return f"https://{jitsi_domain}/{self.jitsi_room_name}"

    def save(self, *args, **kwargs):

        if not self.jitsi_room_name:
            clean_slug = slugify(self.title)
            clean_slug = re.sub(r'[^a-zA-Z0-9-]', '', clean_slug)
            unique_suffix = uuid.uuid4().hex[:8]
            self.jitsi_room_name = f"kanzen-{clean_slug}-{unique_suffix}"
        super().save(*args, **kwargs)