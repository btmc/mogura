from django.db import models
from django.contrib.auth.models import User
import scheduler.models 
from reports.models import token, queue

import datetime

class schedule(models.Model):
	def __unicode__(self):
		return unicode(self.id)

	schedule = models.ForeignKey(scheduler.models.schedule)
	ts = models.DateTimeField(auto_now_add=True)
        status = models.NullBooleanField(null=True)
        error = models.TextField(blank=True, null=True)

class report(models.Model):
	def __unicode__(self):
		return unicode(self.id)
	
	token = models.ForeignKey(token, related_name='+')
        user = models.ForeignKey(User, related_name='logger_report_user+', null=True)
        ts = models.DateTimeField(auto_now_add=True)
        reset_cache = models.NullBooleanField(null=True)
        is_cached = models.NullBooleanField(null=True)
        rc_exists = models.NullBooleanField(null=True)
        send_email = models.BooleanField(default=False)
	schedule = models.ForeignKey(schedule, null=True)

class job_body(models.Model):
	def __unicode__(self):
		return unicode(self.body)

	body = models.TextField(blank=True, null=True)

class job(models.Model):
	def __unicode__(self):
		return unicode(self.id)

        def level(self):
                return min([job.level() + 1 for job in self.job_set.all()] or [0])

	ts_queue = models.DateTimeField(auto_now_add=True, null=True)
        ts_start = models.DateTimeField(null=True)
        ts_finish = models.DateTimeField(null=True)
        status = models.NullBooleanField(null=True)
	body = models.OneToOneField(job_body, null=True)
        error = models.TextField(blank=True, null=True)
	blocking_jobs = models.ManyToManyField('self', symmetrical=False)
	ttr = models.IntegerField(null=True)
        priority = models.BigIntegerField(null=True)
	report = models.ForeignKey(report)
	is_meta = models.BooleanField(default=False)
        queue = models.ForeignKey(queue)
