from django.conf import settings
from django.utils import timezone


def local_now():
    return timezone.localtime(timezone.now(), settings.FORM_TZ_INFO)


def raise_if(expression, error):
    if expression:
        raise error
