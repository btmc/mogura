# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ts_queue', models.DateTimeField(auto_now_add=True, null=True)),
                ('ts_start', models.DateTimeField(null=True)),
                ('ts_finish', models.DateTimeField(null=True)),
                ('status', models.NullBooleanField()),
                ('error', models.TextField(null=True, blank=True)),
                ('ttr', models.IntegerField(null=True)),
                ('priority', models.BigIntegerField(null=True)),
                ('is_meta', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='job_body',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ts', models.DateTimeField(auto_now_add=True)),
                ('reset_cache', models.NullBooleanField()),
                ('is_cached', models.NullBooleanField()),
                ('rc_exists', models.NullBooleanField()),
                ('send_email', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='schedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ts', models.DateTimeField(auto_now_add=True)),
                ('status', models.NullBooleanField()),
                ('error', models.TextField(null=True, blank=True)),
            ],
        ),
    ]
