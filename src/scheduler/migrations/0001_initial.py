# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields
import datetime
from django.conf import settings
import scheduler.models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='chain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(null=True, blank=True)),
                ('report', mptt.fields.TreeForeignKey(related_name='+', to='reports.report')),
                ('report_dependency', mptt.fields.TreeForeignKey(related_name='+', to='reports.report')),
            ],
        ),
        migrations.CreateModel(
            name='schedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_time', models.DateTimeField(default=datetime.datetime.now, blank=True)),
                ('modifier', models.CharField(max_length=100)),
                ('emails', models.TextField(null=True, blank=True)),
                ('send_empty_result', models.BooleanField()),
                ('params_form', models.TextField(null=True, verbose_name=b'Custom params', blank=True)),
                ('retries', models.IntegerField(null=True, blank=True)),
                ('precheck_sql', scheduler.models.NullableCharField(max_length=4096, null=True, blank=True)),
                ('precheck_modifier', scheduler.models.NullableCharField(max_length=100, null=True, blank=True)),
                ('precheck_last_time', models.DateTimeField(null=True, blank=True)),
                ('skip_past_run_times', models.BooleanField(default=True)),
                ('maintainers', models.ManyToManyField(related_name='_schedule_maintainers_+', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('queue', models.ForeignKey(blank=True, to='reports.queue', null=True)),
                ('report', mptt.fields.TreeForeignKey(to='reports.report')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='chain',
            name='schedule',
            field=models.ForeignKey(to='scheduler.schedule'),
        ),
    ]
