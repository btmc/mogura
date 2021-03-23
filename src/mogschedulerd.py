#!/usr/bin/env python
# coding: utf-8

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from settings import *
from settings_local import *

import django
django.setup()

import sys, time
import csv, beanstalkc, json, md5, binascii, datetime
from daemon import Daemon

from scheduler.models import schedule, chain
import logger.models
import reports.models
import reports.views

from datetime import datetime

from django import template
import re
import itertools

from dateutil.relativedelta import relativedelta

import collections

import traceback

from moguemail import MoguraEmail

from django.core import urlresolvers

import psycopg2

import context

from django.contrib.sites.shortcuts import get_current_site

class MoguraSchedulerDaemon(Daemon):
	
        retries_on_schedule_error = 3

	def populate_params(self, params_form):
		cleared_data = {}
		try:
			for i in params_form:
				try:
					if 'initial' in params_form[i]['params']:
        					cleared_data[i] = params_form[i]['params']['initial']
					elif 'required' in params_form[i]['params']:
						if params_form[i]['params']['required'] == False:
							cleared_data[i] = None
				except:
					pass			
		except:
			pass	

		return cleared_data 	
	
	def run(self):
		def modifier_to_dict(modifier):
			re_template = '((?P<%ss>(\+|\-|)[0-9]+)\s+%s)?'
			primitives = [ 'second', 'minute', 'hour', 'day', 'month' ]
			
			return dict([x,int(y if y else 0)] for x,y in dict(itertools.chain(*map(lambda x: x.groupdict().items(), map(re.search, [re_template % (x,x) for x in primitives], [modifier for x in range(len(primitives))])))).iteritems())

		while True:
			for item in schedule.objects.raw(
                                                '''
                                                    select
                                                        *
                                                    from
                                                        scheduler_schedule
                                                    where
                                                        modifier_apply
                                                            (
                                                                (
                                                                    select
                                                                        last_time
                                                                    union
                                                                    select
                                                                        precheck_last_time
                                                                    order by
                                                                        1   desc
                                                                    limit
                                                                        1
                                                                ),
                                                                modifier
                                                            )
                                                    <
                                                        now()
                                                    and
                                                        is_active
                                                '''
                                            ):
                                try:
					logger_schedule = logger.models.schedule(schedule = item)
					logger_schedule.save()

					interval = relativedelta(**modifier_to_dict(item.modifier))

                                        if item.precheck_sql != None:
					        precheck_interval = relativedelta(**modifier_to_dict(item.precheck_modifier if item.precheck_modifier != None else item.modifier))

						params = self.populate_params(item.report.params_form_evaluated())
						params.update(item.params_form_evaluated())

						sql = template.Template(item.precheck_sql).render(context.SafeContext(params))

                                                pgsql_conn = psycopg2.connect(PGSQL_DSN)

                                                pgsql_cursor = pgsql_conn.cursor()
                                                pgsql_cursor.execute(sql)

                                                result = pgsql_cursor.fetchone()[0]

                                                pgsql_cursor.close()
                                                pgsql_conn.close()

                                                if not result:
                                                        item.precheck_last_time = datetime.now() - interval + precheck_interval

                                                        item.save()
 
                                                        logger_schedule.status = False
                                                        logger_schedule.error = 'Precheck condition failed.'

                                                        continue

                                        if item.skip_past_run_times:
                                                while item.last_time + interval < datetime.now() - interval:
                                                        item.last_time += interval 

                                        item.last_time += interval

		                        beanstalk_conn = beanstalkc.Connection(host=BEANSTALK_HOST, port=BEANSTALK_PORT)

					emails = ','.join([i.email for i in item.users.all()]) + (',' + item.emails if item.emails else '')
					maintainers_emails = ','.join([i.email for i in item.maintainers.all()])

					run_item_sets = collections.OrderedDict({item.report.id: {'report': item.report, 'report_dependency': None}, })

					for chain_item in chain.objects.filter(schedule = item.id):
						run_item_sets[chain_item.report_id] = {'report': chain_item.report, 'report_dependency': chain_item.report_dependency}

					for i, run_item_set in run_item_sets.items():
						params = self.populate_params(run_item_set['report'].params_form_evaluated())
						params.update(item.params_form_evaluated())

                                                sql = run_item_set['report'].sql_evaluated()

                                                params.update({'token': '{{token}}'})

						sql = template.Template(sql).render(context.SafeContext(params))
						token = binascii.hexlify(md5.new(sql.encode('utf-8')).digest())

                                                params.update({'token': token})

						sql = template.Template(sql).render(context.SafeContext(params))
						token = binascii.hexlify(md5.new(sql.encode('utf-8')).digest())

						run_item_sets[i]['params'] = params
						run_item_sets[i]['sql'] = sql
						run_item_sets[i]['token'] = token	

					for i, run_item_set in run_item_sets.items():
						params = run_item_set['params'] 
						sql = run_item_set['sql'] 
						token = run_item_set['token']

						job_body = json.dumps({'sql': sql, 'token': token, 'title': template.Template(run_item_set['report'].title_email).render(context.SafeContext(params)), 'title_csv': template.Template(run_item_set['report'].title_csv).render(context.SafeContext(params)), 'emails': emails, 'maintainers_emails': maintainers_emails, 'send_empty_result': item.send_empty_result, 'message': template.Template(run_item_set['report'].title).render(context.SafeContext(params))})

						try:
							blocking_job = logger.models.job.objects.get(pk=reports.models.token.objects.get(pk=run_item_sets[run_item_set['report_dependency'].id]['token']).job_id)
						except:
							blocking_job = None	

						job_attrs = {}
						job_attrs['ttr'] = BEANSTALK_TTR
						if run_item_set['report'].job_priority != None:
							job_attrs['priority'] = run_item_set['report'].job_priority 

						token_item, is_created = reports.models.token.objects.get_or_create(pk=token, report=reports.models.report.objects.get(pk=run_item_set['report'].id))
						token_item.dictionary = json.dumps({key:params[key] for key in params if key!='reset_cache'}, cls=reports.views.CustomEncoder)
	
                                                queue = item.queue or run_item_set['report'].queue					
		                                beanstalk_conn.use(queue)

						job_id = beanstalk_conn.put(job_body, **job_attrs)

						token_item.job_id = job_id
						token_item.save()

						logger_report = logger.models.report(token = token_item, user=None, reset_cache = True, is_cached = False, rc_exists = False, send_email = True, schedule = logger_schedule)
						logger_report.save()

                                                with django.db.transaction.atomic():
                                                        job_body_item = logger.models.job_body(id = job_id, body = job_body)
                                                        job_body_item.save()

                                                        job_item = logger.models.job(id = job_id, body = job_body_item, ttr = job_attrs['ttr'], priority = job_attrs['priority'] if 'priority' in job_attrs else None, report = logger_report, queue = reports.models.queue.objects.get_or_create(title = queue)[0])
                                                        job_item.save()

                                                        if blocking_job:
                                                                job_item.blocking_jobs.add(blocking_job)

                                                        job_item.save()
						
                                        item.retries = self.retries_on_schedule_error

					item.save()

                                        logger_schedule.status = True

                                except Exception, e:
                                        try:
                                                retries_left = (item.retries if item.retries != None else self.retries_on_schedule_error) - 1

                                                if retries_left > 0:
                                                        item.retries = retries_left
                                                else:
                                                        while item.last_time + interval < datetime.now():
                                                                item.last_time += interval 

                                                        item.retries = 1

                                                item.save()
                                        except:
                                                pass
                                               
                                        error_message = unicode(traceback.format_exc(), errors='replace')[:65535]
                                        logger_schedule.error = error_message 

                                        logger_schedule.status = False

                                        try:
                                                maintainers_emails = ','.join([i.email for i in item.maintainers.all()])
                                                scheduler_url = 'http://' + str(get_current_site(None)) + urlresolvers.reverse('admin:scheduler_schedule_change', args=(item.id,))
                                                MoguraEmail().send(u'Ошибка запуска отчета по расписанию', u'<b>Отчет:</b><br/><br/>' + item.report.title_menu_hier() + ' (id ' + str(item.report.id) + ')' + '<br/><br/>' + u'<b>Ошибка:</b><br/><br/>' + error_message + '</a>' + '<br/><br/><a href="' + scheduler_url + '">' + scheduler_url + '</a>', maintainers_emails)
                                        except:
                                                pass

                                finally:
                                        logger_schedule.save()

			time.sleep(10)	

if __name__ == "__main__":
	if len(sys.argv) < 1:
		print "usage: python %s start|stop|restart" % sys.argv[0]
		print "example: python %s start ordinary" % sys.argv[0]
		sys.exit(2)

	daemon = MoguraSchedulerDaemon('/var/run/mogura-schedulerd.pid')

	if 'start' == sys.argv[1]:
		daemon.start()
	elif 'stop' == sys.argv[1]:
		daemon.stop()
	elif 'restart' == sys.argv[1]:
		daemon.restart()
	else:
		print "Unknown command"
		sys.exit(2)
	sys.exit(0)

