# Generated by Django 3.2.5 on 2021-10-17 12:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IdempotencyKey',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('idempotency_key', models.UUIDField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_run_at', models.DateTimeField(auto_now=True)),
                ('locked_at', models.DateTimeField(null=True)),
                ('request_method', models.CharField(max_length=16)),
                ('request_params', models.TextField()),
                ('request_path', models.CharField(max_length=255)),
                ('request_digest', models.BinaryField(max_length=32)),
                ('response_code', models.PositiveSmallIntegerField(null=True)),
                ('response_body', models.TextField(null=True)),
                (
                    'recovery_point',
                    models.CharField(
                        choices=[('started', 'started'), ('finished', 'finished')], default='started', max_length=64
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                'db_table': 'idempotency_key',
            },
        ),
        migrations.AddConstraint(
            model_name='idempotencykey',
            constraint=models.UniqueConstraint(
                fields=('user', 'idempotency_key'), name='Unique IdempotencyKey (user, idempotency_key)'
            ),
        ),
    ]