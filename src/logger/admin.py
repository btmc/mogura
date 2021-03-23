# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from logger.models import report, job, schedule 

from django.contrib import admin
from django import template

import json, datetime


def render_url(entity, title = None, id = None):
	return template.Template('<a target=_blank href="{% url url id %}">{{title}}</a>').render(template.Context({'url': 'admin:' + entity._meta.app_label + '_' + entity._meta.model_name + '_change', 'id': id if id else entity.id, 'title': title if title else entity})) if entity else None


class reportAdmin (admin.ModelAdmin):
        class Media:
                css = {
                        all: ('admin.css',)
                }

    	def has_add_permission(self, request):
		return False

    	def has_delete_permission(self, request, obj=None):
		return False

	def token_url(self, report):
		entity = report.token
		return render_url(entity, title = entity.dictionary[:100] + (entity.dictionary[100:] and '...'), id = entity.token)

	token_url.allow_tags = True
	token_url.short_description = 'params'

	def report_url(self, report):
		entity = report.token.report
		return render_url(entity, title = entity.title_menu_hier())

	report_url.allow_tags = True

	def schedule_url(self, report):
		return render_url(report.schedule)

	schedule_url.allow_tags = True
	schedule_url.short_description = 'schedule'

	def job_urls(self, report):
		res = []

                def insert_job(job_item):
                    if res.count(job_item) == 0: 
                        try:
                            res.insert(res.index(sorted(job_item.job_set.all(), key=job.level)[0]) + 1, job_item)
                        except:
                            res.append(job_item)

                for job_item in sorted(report.job_set.all(), key=job.level):
                    insert_job(job_item)

                img_yes = '<img src="/static/admin/img/icon-yes.gif" alt="True" />'
                img_no = '<img src="/static/admin/img/icon-no.gif" alt="False" />'

                return '<br/>'.join(['<span style="white-space: nowrap;">%s%s %s</span>' % ('-'*job_item.level(), render_url(job_item), img_yes if job_item.status else img_no) for job_item in res]) 

	job_urls.allow_tags = True
	job_urls.short_description = 'job list'

	def direct_url(self, report):
		return '<a target="_blank" href="%s">результат</a>' % report.token.direct_url()

	direct_url.allow_tags = True

	def job_status(self, report):
		res = True
		for job in report.job_set.all():
			res = res and job.status
		
		return res

	job_status.boolean = True 

        actions = None
        list_display = ('ts', 'report_url', 'token_url', 'direct_url', 'user', 'reset_cache', 'is_cached', 'rc_exists', 'send_email', 'schedule_url', 'job_urls', 'job_status',)
	list_display_links = ('ts',)
        readonly_fields = ('job_urls', 'ts', 'user', 'token_url', 'reset_cache', 'is_cached', 'rc_exists', 'send_email', 'schedule',)
	exclude = ('token',)
        list_filter = ('ts', 'user',)
        ordering = ('-ts',)

class scheduleAdmin (admin.ModelAdmin):
    	def has_add_permission(self, request):
		return False

    	def has_delete_permission(self, request, obj=None):
		return False

	def report_url(self, schedule):
		res = [] 
		for item in schedule.report_set.all():
			res.append(render_url(item))

		return ','.join(res)

	report_url.allow_tags = True

	def schedule_url(self, schedule):
		entity = schedule.schedule 
		return render_url(entity)

	schedule_url.allow_tags = True

	def job_status(self, schedule):
		res = True
		for item in schedule.report_set.all():
			for job in item.job_set.all():
				res = res and job.status

		return res

	job_status.boolean = True 

        actions = None
        list_display = ('ts', 'schedule_url', 'report_url', 'status', 'job_status',)
	readonly_fields = ('ts', 'schedule', 'status', 'error',)
        list_filter = ('ts',)
        ordering = ('-ts',)

class jobAdmin (admin.ModelAdmin):
    	def has_add_permission(self, request):
		return False

    	def has_delete_permission(self, request, obj=None):
		return False

        def ts_delta(self, job_item):
                if not job_item.ts_start:
                        return None
		
		if not job_item.ts_finish:
			return template.Template('<font color="gray">{{ts}}</font>').render(template.Context({'ts': datetime.datetime.now() - job_item.ts_start}))

                return job_item.ts_finish - job_item.ts_start

	ts_delta.allow_tags = True

	def direct_url(self, job_item):
		return '<a target="_blank" href="%s">результат</a>' % job_item.report.token.direct_url()

	direct_url.allow_tags = True

	def report_url(self, job_item):
		entity = job_item.report
		return render_url(entity)

	report_url.allow_tags = True

	def blocking_jobs_urls(self, job_item):
		res = []
		for job in job_item.blocking_jobs.all():
			res += [render_url(job)]

		return ', '.join(res)

	blocking_jobs_urls.allow_tags = True
	blocking_jobs_urls.short_description = 'blocking jobs'

        actions = None
        list_display = ('id', 'ts_queue', 'ts_start', 'ts_finish', 'ts_delta', 'direct_url', 'blocking_jobs_urls', 'report_url', 'priority', 'status', 'is_meta', 'queue')
	readonly_fields = ('id', 'ts_queue', 'ts_start', 'ts_finish', 'body', 'status', 'error', 'ttr', 'priority', 'report', 'blocking_jobs', 'is_meta', 'queue')
        list_filter = ('ts_start', 'status', 'queue')
        ordering = ('-id',)

admin.site.register(report, reportAdmin)
admin.site.register(job, jobAdmin)
admin.site.register(schedule, scheduleAdmin)
