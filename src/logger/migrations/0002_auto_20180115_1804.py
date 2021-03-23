# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0001_initial'),
        ('reports', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scheduler', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='schedule',
            field=models.ForeignKey(to='scheduler.schedule'),
        ),
        migrations.AddField(
            model_name='report',
            name='schedule',
            field=models.ForeignKey(to='logger.schedule', null=True),
        ),
        migrations.AddField(
            model_name='report',
            name='token',
            field=models.ForeignKey(related_name='+', to='reports.token'),
        ),
        migrations.AddField(
            model_name='report',
            name='user',
            field=models.ForeignKey(related_name='logger_report_user+', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='blocking_jobs',
            field=models.ManyToManyField(to='logger.job', null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='body',
            field=models.OneToOneField(null=True, to='logger.job_body'),
        ),
        migrations.AddField(
            model_name='job',
            name='queue',
            field=models.ForeignKey(to='reports.queue'),
        ),
        migrations.AddField(
            model_name='job',
            name='report',
            field=models.ForeignKey(to='logger.report'),
        ),
    ]
