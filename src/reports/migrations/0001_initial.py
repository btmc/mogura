# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='euser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='queue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('priority', models.IntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('job_priority', models.IntegerField(null=True, blank=True)),
                ('title_menu', models.TextField(blank=True)),
                ('title_csv', models.TextField(blank=True)),
                ('title_email', models.TextField(blank=True)),
                ('title', models.TextField()),
                ('title_caption', models.TextField(blank=True)),
                ('sql', models.TextField(blank=True)),
                ('params_form', models.TextField(null=True, blank=True)),
                ('conflicts', models.TextField(null=True, blank=True)),
                ('groups', models.TextField(null=True, blank=True)),
                ('reset_cache', models.BooleanField(default=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('xls_charts_udf', models.TextField(null=True, blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, to='reports.report', null=True)),
                ('queue', models.ForeignKey(to='reports.queue')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='report_subreports',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(null=True, blank=True)),
                ('params_form', models.TextField(null=True, verbose_name=b'Custom initial values for params', blank=True)),
                ('report', models.ForeignKey(related_name='+', to='reports.report')),
                ('subreport', mptt.fields.TreeForeignKey(related_name='dependencies', on_delete=django.db.models.deletion.PROTECT, to='reports.report')),
            ],
            options={
                'verbose_name': 'Subreport',
            },
        ),
        migrations.CreateModel(
            name='role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='token',
            fields=[
                ('token', models.CharField(max_length=32, serialize=False, primary_key=True)),
                ('dictionary', models.TextField(default=b'{}', blank=True)),
                ('job_id', models.IntegerField(null=True)),
                ('report', models.ForeignKey(to='reports.report')),
            ],
        ),
        migrations.AddField(
            model_name='report',
            name='roles',
            field=models.ManyToManyField(to='reports.role'),
        ),
        migrations.AddField(
            model_name='report',
            name='subreports',
            field=models.ManyToManyField(related_name='dependent_reports', through='reports.report_subreports', to='reports.report'),
        ),
        migrations.AddField(
            model_name='report',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='euser',
            name='roles',
            field=models.ManyToManyField(to='reports.role'),
        ),
        migrations.AddField(
            model_name='euser',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='report_subreports',
            unique_together=set([('report', 'subreport')]),
        ),
    ]
