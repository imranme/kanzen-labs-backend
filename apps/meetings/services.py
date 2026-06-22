import requests
from django.conf import settings

HMS_API_BASE = "https://api.100ms.live/v2"


def _headers():
    return {
        "Authorization": f"Bearer {settings.HMS_MANAGEMENT_TOKEN}",
        "Content-Type": "application/json",
    }


def create_hms_room(meeting_title: str) -> dict:
    if not getattr(settings, "HMS_MANAGEMENT_TOKEN", ""):
        return {
            "room_id":      "",
            "meeting_link": "https://meet.kanzenlabs.io/pending-100ms-setup",
        }

    response = requests.post(
        f"{HMS_API_BASE}/rooms",
        headers=_headers(),
        json={
            "name":        meeting_title[:50],
            "description": meeting_title,
            "template_id": settings.HMS_TEMPLATE_ID,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    room_id = data["id"]
    subdomain = getattr(settings, "HMS_SUBDOMAIN", "yourapp.app.100ms.live")

    return {
        "room_id":      room_id,
        "meeting_link": f"https://{subdomain}/meeting/{room_id}",
    }


def get_join_token(room_id: str, user_id: str, user_name: str, role: str = "host") -> str:
    if not room_id or not getattr(settings, "HMS_MANAGEMENT_TOKEN", ""):
        return ""

    response = requests.post(
        f"{HMS_API_BASE}/room-codes/room/{room_id}",
        headers=_headers(),
        timeout=10,
    )
    response.raise_for_status()
    codes = response.json().get("data", [])

    matching = next((c for c in codes if c.get("role") == role), None)
    code = matching["code"] if matching else (codes[0]["code"] if codes else "")

    return code


def end_hms_room(room_id: str):
    if not room_id or not getattr(settings, "HMS_MANAGEMENT_TOKEN", ""):
        return
    requests.post(
        f"{HMS_API_BASE}/active-rooms/{room_id}/end-room",
        headers=_headers(),
        json={"reason": "Meeting completed", "lock": True},
        timeout=10,
    )