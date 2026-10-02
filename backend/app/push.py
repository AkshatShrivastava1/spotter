"""Expo push notifications (works for iOS + Android through Expo's push service)."""

import logging

import httpx

from .config import get_settings
from .models import Notification, User

log = logging.getLogger(__name__)
EXPO_URL = "https://exp.host/--/api/v2/push/send"


def send_push(user: User, n: Notification) -> bool:
    if not (get_settings().expo_push_enabled and user.push_token):
        return False
    try:
        r = httpx.post(EXPO_URL, json={"to": user.push_token, "title": n.title, "body": n.body,
                                       "data": {"kind": n.kind, "id": n.id}, "sound": "default"},
                       timeout=10)
        return r.status_code == 200
    except Exception as e:  # pragma: no cover
        log.warning("push failed: %s", e)
        return False
