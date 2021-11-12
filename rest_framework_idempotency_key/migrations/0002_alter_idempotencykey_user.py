# Generated by Django 3.2.5 on 2021-11-12 02:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rest_framework_idempotency_key', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='idempotencykey',
            name='user',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
