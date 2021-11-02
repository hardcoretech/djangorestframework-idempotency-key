import operator
from functools import partial, wraps

from data_spec_validator.decorator import dsv_request_meta
from data_spec_validator.spec import UUID, Checker
from rest_framework.request import Request
from rest_framework.response import Response

from .middleware import IdempotencyKeyMiddleware
from .models import IDEMPOTENCY_RECOVERY_POINT_FINISHED, IDEMPOTENCY_RECOVERY_POINT_STARTED
from .utils import raise_if


class _IdempotencyKeyRequestMetaSpec:
    HTTP_IDEMPOTENCY_KEY = Checker([UUID])


idempotency_key_validation = partial(dsv_request_meta, spec=_IdempotencyKeyRequestMetaSpec)


def simple_idempotency_key_method(func):
    return simple_idempotency_key_method_ex(request_getter=operator.itemgetter(1))(func)


def simple_idempotency_key_method_ex(request_getter):
    def decorator(func):
        @wraps(func)
        @idempotency_key_validation()
        def wrapper(*args, **kwargs):
            request = request_getter(args)
            raise_if(not isinstance(request, Request), TypeError('Only supports a DRF Request instance'))

            def action():
                response = func(*args, **kwargs)
                raise_if(not isinstance(response, Response), TypeError('Only supports a DRF Response instance'))

                return (
                    response.status_code,  # response_code
                    response.data,  # response_body
                    IDEMPOTENCY_RECOVERY_POINT_FINISHED,  # next recovery_point
                )

            raise_if(
                request.idempotency_key is None,
                AttributeError('Attribute: idempotency_key not found in request instance'),
            )
            raise_if(
                request.idempotency_key.recovery_point
                not in (
                    IDEMPOTENCY_RECOVERY_POINT_STARTED,
                    IDEMPOTENCY_RECOVERY_POINT_FINISHED,
                ),
                RuntimeError(f'Unexpected recovery point: {request.idempotency_key.recovery_point}'),
            )

            idempotency_key = request.idempotency_key

            recovery_point_to_action_map = {
                IDEMPOTENCY_RECOVERY_POINT_STARTED: action,
            }
            response_code, response_body, recovery_point = IdempotencyKeyMiddleware.proceed(
                idempotency_key, recovery_point_to_action_map
            )

            raise_if(
                recovery_point != IDEMPOTENCY_RECOVERY_POINT_FINISHED,
                RuntimeError('recovery_point must be in finished state'),
            )
            return Response(response_body, status=response_code)

        return wrapper

    return decorator
