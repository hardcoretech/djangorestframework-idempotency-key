import hashlib
import json
from datetime import timedelta
from typing import Any, Callable, Dict, Tuple

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.utils.encoders import JSONEncoder

from .models import (
    IDEMPOTENCY_RECOVERY_POINT_FINISHED,
    IDEMPOTENCY_RECOVERY_POINT_STARTED,
    IdempotencyKey,
    RecoveryPoint,
)
from .utils import raise_if


class IdempotencyKeyMiddleware:
    EXEMPT_STATUS_LIST = (status.HTTP_400_BAD_REQUEST,)

    class Http409Error(Exception):
        def __init__(self, message=''):
            self.message = message

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.idempotency_key = self._prepare_idempotency_key(request)
        except self.Http409Error as exc:
            return JsonResponse({'message': exc.message}, status=status.HTTP_409_CONFLICT)

        try:
            response = self.get_response(request)
        finally:
            self._reset_lock(request)

        return response

    @staticmethod
    def make_digest(request_method, request_params, request_path):
        sha256 = hashlib.sha256()
        sha256.update(request_method)
        sha256.update(request_path)
        sha256.update(request_params)
        return sha256.digest()

    @transaction.atomic
    def _prepare_idempotency_key(self, request):
        if 'Idempotency-Key' not in request.headers:
            return None

        if request.method.upper() not in ('PATCH', 'POST', 'PUT'):
            return None

        idempotency_key = request.headers['Idempotency-Key']
        digest = self.make_digest(
            request.method.encode('utf8'),
            request.body,
            request.path_info.encode('utf8'),
        )

        obj, created = IdempotencyKey.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                'request_method': request.method,
                'request_params': request.body,
                'request_path': request.path_info,
                'request_digest': digest,
                'recovery_point': IDEMPOTENCY_RECOVERY_POINT_STARTED,
                'locked_at': timezone.now(),
            },
        )

        if not created:
            # prevent 2 non-created clients from acquiring `locked_at`
            obj = IdempotencyKey.objects.select_for_update().get(idempotency_key=idempotency_key)

            # Programs sending multiple requests with different parameters but the
            # same idempotency key is a bug.
            if obj.request_digest != digest:
                raise self.Http409Error('Parameter mismatch, please reload page.')

            # Only acquire a lock if the key is unlocked or its lock has expired
            # because the original request was long enough ago.
            if obj.locked_at and obj.locked_at > timezone.now() - timedelta(
                seconds=settings.IDEMPOTENCY_KEY_LOCK_TIMEOUT
            ):
                raise self.Http409Error(
                    'Request in progress, please try again later.',
                )

            # Lock the key and update latest run unless the request is already
            # finished
            if obj.recovery_point != IDEMPOTENCY_RECOVERY_POINT_FINISHED:
                obj.locked_at = timezone.now()
                obj.save(update_fields=['last_run_at', 'locked_at'])

        return obj

    def _reset_lock(self, request):
        if request.idempotency_key is None or request.idempotency_key.locked_at is None:
            return

        if request.idempotency_key.response_code in self.EXEMPT_STATUS_LIST:
            request.idempotency_key.delete()
            return

        request.idempotency_key.locked_at = None
        request.idempotency_key.save(update_fields=['locked_at'])

    TRecoveryPointAction = Tuple[int, Any, str]
    TRecoveryPointToActionMap = Dict[RecoveryPoint, Callable[[], TRecoveryPointAction]]

    @staticmethod
    def proceed(idempotency_key: IdempotencyKey, recovery_point_to_action_map: TRecoveryPointToActionMap):
        raise_if(idempotency_key is None, AssertionError('Parameter idempotency_key cannot be None'))

        response_code, response_body, recovery_point = (
            idempotency_key.response_code,
            idempotency_key.response_body,
            idempotency_key.recovery_point,
        )
        while recovery_point != IDEMPOTENCY_RECOVERY_POINT_FINISHED:
            action = recovery_point_to_action_map[idempotency_key.recovery_point]
            with transaction.atomic():
                response_code, response_body, recovery_point = action()

                if recovery_point == IDEMPOTENCY_RECOVERY_POINT_FINISHED:
                    idempotency_key.response_code = response_code
                    idempotency_key.response_body = json.dumps(
                        response_body, ensure_ascii=False, indent=None, separators=(',', ':'), cls=JSONEncoder
                    )
                idempotency_key.recovery_point = recovery_point
                idempotency_key.save(update_fields=['response_code', 'response_body', 'recovery_point'])

        return idempotency_key.response_code, json.loads(idempotency_key.response_body), idempotency_key.recovery_point
