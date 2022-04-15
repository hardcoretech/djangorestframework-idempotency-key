from django.db import models

# Please read https://brandur.org/idempotency-keys for more detail.
#
# `idempotency_key` is an UUID generated by client, used for prevent re-send identical API multiple times accidentally.
# The mechanism is designed to present a multi-stage, resume-able architecture.


IDEMPOTENCY_RECOVERY_POINT_STARTED = 'started'
IDEMPOTENCY_RECOVERY_POINT_FINISHED = 'finished'


# Customizable recovery points, feel free to add your own custom recovery points for different stages,
# but please keep started/finished as the very first/last stages.
class RecoveryPoint(models.TextChoices):
    STARTED = IDEMPOTENCY_RECOVERY_POINT_STARTED, IDEMPOTENCY_RECOVERY_POINT_STARTED
    FINISHED = IDEMPOTENCY_RECOVERY_POINT_FINISHED, IDEMPOTENCY_RECOVERY_POINT_FINISHED


class IdempotencyKey(models.Model):
    id = models.AutoField(primary_key=True)
    idempotency_key = models.UUIDField()

    created_at = models.DateTimeField(auto_now_add=True)
    last_run_at = models.DateTimeField(auto_now=True)
    locked_at = models.DateTimeField(null=True)

    request_method = models.CharField(max_length=16)
    request_params = models.TextField()
    request_path = models.CharField(max_length=255)
    request_digest = models.BinaryField(max_length=32)

    response_code = models.PositiveSmallIntegerField(null=True)
    response_body = models.TextField(null=True)

    recovery_point = models.CharField(
        max_length=64,
        default=RecoveryPoint.STARTED.value,
        choices=RecoveryPoint.choices,
    )

    class Meta:
        db_table = 'idempotency_key'
        constraints = [
            models.UniqueConstraint(fields=['idempotency_key'], name='Unique IdempotencyKey (idempotency_key)')
        ]
