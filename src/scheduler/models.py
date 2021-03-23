# coding: utf-8

from django.db import models

from reports.models import report, queue

from django.contrib.auth.models import User

from mptt.models import TreeForeignKey

import json

from datetime import *

import exec_helpers as eh

import collections

class NullableCharField(models.CharField):
        def get_db_prep_value(self, value, connection, prepared=False):
                if value == '':
                        return None

                return value

class schedule(models.Model):
	is_active=models.BooleanField(default=True)
        queue=models.ForeignKey(queue, blank=True, null=True)
	last_time=models.DateTimeField(default=datetime.now, blank=True)
	modifier=models.CharField(max_length=100)
	report=TreeForeignKey(report)
	users=models.ManyToManyField(User)
	emails=models.TextField(blank=True, null=True)
	send_empty_result=models.BooleanField()
	maintainers=models.ManyToManyField(User, related_name='scheduler_schedule_maintainers+')
	params_form = models.TextField(blank=True, null=True, verbose_name='Custom params')
	retries=models.IntegerField(blank=True, null=True)
        precheck_sql = NullableCharField(max_length=4096, blank=True, null=True)
        precheck_modifier = NullableCharField(max_length=100, blank=True, null=True)
        precheck_last_time = models.DateTimeField(blank=True, null=True)
        skip_past_run_times = models.BooleanField(default=True)

        def params_form_evaluated(self):
                try:
                        res = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(self.params_form)

			def _(i, ns):
				if i in res:
					if type(res[i]) == str or type(res[i]) == unicode:
						if res[i].find('exec ') == 0:
							res[i] = res[i].replace('exec ', 'res[i] = ', 1)
							exec res[i] in globals(), dict(ns.items() + locals().items())

					return res[i]

                        for i in res:
                                try:
					_(i, locals())
                                except:
                                        raise

                        return res
                except:
                        return None

	def menu_title(self):
		return self.report.title_menu_hier()

	def users_list(self):
		return ", ".join([i.username for i in self.users.all()])

	def last_time_f(self):
		return self.last_time.strftime('%Y-%m-%d %H:%M:%S') 

	last_time_f.short_description = 'Last run time'

	def __unicode__(self):
		return self.menu_title()

class chain(models.Model):
	schedule = models.ForeignKey(schedule)
	order  = models.IntegerField(blank=True, null=True)
	report_dependency = TreeForeignKey(report, related_name='+')
	report = TreeForeignKey(report, related_name='+')
