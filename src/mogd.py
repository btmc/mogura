#!/usr/bin/env python
# coding: utf-8
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from settings import *
from settings_local import *

import django
django.setup()

import sys, time, re, codecs, datetime, traceback
import psycopg2, csv, beanstalkc, json
from daemon import Daemon
from moguemail import MoguraEmail

from csv2xls import csv2xls
from csv2html import csv2html

import logger.models
import reports.models

from django.core import urlresolvers
from django.db import transaction

from comegakure import *

from reports.views import sql_to_token, get_csv_filename, get_xls_filename

from django.contrib.sites.shortcuts import get_current_site

class MoguraDaemon(Daemon):
	store_dir = STORE_DIR 

	pgsql_conn = None
	beanstalk_conn = None

	message_line_limit = 200
	job_release_delay = 1
	job_max_orphan_age = 300

	def pgsql_connect(self):
		self.pgsql_conn = psycopg2.connect(PGSQL_DSN)	

	def beanstalk_connect(self):
		self.beanstalk_conn = beanstalkc.Connection(host=BEANSTALK_HOST, port=BEANSTALK_PORT)

                beanstalk_queues = self.beanstalk_queues[:]
		while beanstalk_queues:
			self.beanstalk_conn.watch(beanstalk_queues.pop())

	def __init__(self, pidfile, beanstalk_queues):
		self.beanstalk_queues = beanstalk_queues

		super(MoguraDaemon, self).__init__(pidfile)	
	
	def run(self):
		while True:
			try:
				job = self.beanstalk_conn.reserve()
                        except  KeyboardInterrupt:
                                raise
			except:
				try:
					self.beanstalk_connect()
				except:
					pass
				continue	

			try:
				log = logger.models.job.objects.get(pk=job.jid)
				log.ts_start = datetime.datetime.now()
				log.ts_finish = None 
				log.save()

			except:
				if job.stats()['age'] < self.job_max_orphan_age:
					job.release(delay = self.job_release_delay)
				else:
					job.bury()

				continue

			try:
				cur = self.pgsql_conn.cursor()
				cur.execute('select 1')
			except:
				try:
					self.pgsql_connect()
				except:
					job.release()

					log.status = False
					log.error = 'Cannot connect to DB'
					log.ts_finish = datetime.datetime.now()
					log.save()

					time.sleep(1)
			else:
				cur.close()

			try:
				log_savepoint = transaction.savepoint()

				exec 'job_data = json.loads(r"""' + job.body + '""")' in globals(), locals()

				csv_filename = get_csv_filename(job_data['token'])
				xls_filename = get_xls_filename(job_data['token'])

				if not os.path.exists(os.path.dirname(csv_filename)):
					os.makedirs(os.path.dirname(csv_filename))

				temp_csv_filename = self.store_dir + '/tmp-' + str(os.getpid()) + '.csv'
				temp_xls_filename = self.store_dir + '/tmp-' + str(os.getpid()) + '.xlsx'

				#Check the job is not blocked:

				is_blocked = False
				for blocking_job_item in log.blocking_jobs.all(): 
					blocking_job = self.beanstalk_conn.peek(blocking_job_item.id)
					if type(blocking_job) == beanstalkc.Job:
                                                try:
                                                        blocking_job_stats = blocking_job.stats()

                                                        if blocking_job_stats['state'] == 'buried':
                                                                if 'error_emails' in job_data:
                                                                        job_data['error_emails'] = ''

                                                                raise Exception('Blocking job error')
                                                        else:
                                                                is_blocked = True
                                                                break

                                                except beanstalkc.CommandFailed:
                                                        pass


				if is_blocked:
					job.release(delay = self.job_release_delay, priority = min(blocking_job_stats['pri'] + 1, 2**32 - 1))

					log.status = False
					log.error = 'Job released due to blocking job is still active'
					log.ts_finish = datetime.datetime.now()
					log.priority = job.stats()['pri']
					log.save()

					continue	

				#Check if cache can be used:
				use_cache = False	
				if 'use_cache' in job_data and job_data['use_cache'] == True:
			 		if os.path.isfile(xls_filename) and os.path.getsize(xls_filename) > 0:
						use_cache = True
				
				if not use_cache:

					def is_simple_node(node):
						sub_nodes = node.sub_nodes()
                                                try:
						        sub_node = sub_nodes.next()
                                                except:
                                                        return True

						try:
							sub_nodes.next()
						except:
							if type(sub_node) == SimpleNode:
								return True
							else:
								return False
					#			return is_simple_node(sub_node)
						else:
							return False

					job_node = UnknownNode(job_data['sql'])

					if not is_simple_node(job_node):
						sub_nodes = [x for x in job_node.sub_nodes()]

						process_subnodes = False
						if len(sub_nodes) == 1:
							sub_nodes = [x for x in sub_nodes[0].sub_nodes()]
							process_subnodes = True

						if log.is_meta:
							csvfile = open(temp_csv_filename, 'w')
						
							for sub_node in sub_nodes:
								sub_node_csv_filename = get_csv_filename(sql_to_token(sub_node.sql))
								if os.path.isfile(sub_node_csv_filename):
									if csvfile.tell():
										try:
											assert job_data['skip_headers'] == True
										except:
											csvfile.write('\r\n')

									sub_csvfile = open(sub_node_csv_filename)
									csvfile.write(sub_csvfile.read())
									sub_csvfile.close()

							csvfile.close()

							csv2xls(temp_csv_filename, temp_xls_filename, job_data['token'])

							os.rename(temp_csv_filename, csv_filename)
							os.rename(temp_xls_filename, xls_filename)

						else:
							blocking_jobs = log.blocking_jobs.all()

							prev_sub_job_item = None

                                                        with django.db.transaction.atomic():
                                                                for sub_node in sub_nodes:
                                                                        sub_job_body = json.dumps({'sql': sub_node.sql, 'token': sql_to_token(sub_node.sql), 'title': job_data['title'], 'emails': '', 'error_emails': job_data['error_emails'] if 'error_emails' in job_data else '', 'use_cache': job_data['use_cache'] if 'use_cache' in job_data else False, 'skip_headers': prev_sub_job_item != None if type(sub_node) == MultipleNode else job_data['skip_headers'] if 'skip_headers' in job_data else ''})
                                                                        sub_job_attrs = {'ttr': job.stats()['ttr'], 'priority': max(0, job.stats()['pri'] - 1)}

                                                                        self.beanstalk_conn.use(job.stats()['tube'])

                                                                        sub_job_id = self.beanstalk_conn.put(sub_job_body, **sub_job_attrs)

                                                                        sub_job_body_item = logger.models.job_body(id = sub_job_id, body = sub_job_body)
                                                                        sub_job_body_item.save()

                                                                        sub_job_item = logger.models.job(id = sub_job_id, ts_queue = datetime.datetime.now(), body = sub_job_body_item, ttr = sub_job_attrs['ttr'], priority = sub_job_attrs['priority'], report = log.report, queue = reports.models.queue.objects.get_or_create(title = job.stats()['tube'])[0])
                                                                        sub_job_item.save()

                                                                        for blocking_job in blocking_jobs:
                                                                                sub_job_item.blocking_jobs.add(blocking_job)

                                                                        if process_subnodes:
                                                                                log.blocking_jobs.add(sub_job_item)
                                                                        elif prev_sub_job_item:
                                                                                sub_job_item.blocking_jobs.add(prev_sub_job_item)

                                                                        prev_sub_job_item = sub_job_item	

                                                                if not process_subnodes:
                                                                        log.blocking_jobs.add(sub_job_item)
                                                                        
                                                                job.release(delay = self.job_release_delay)

                                                                log.status = False
                                                                log.error = 'Subjobs are scheduled to process, job released.'
                                                                log.ts_finish = datetime.datetime.now()
                                                                log.is_meta = True
                                                                log.save()

                                                        continue
                                        else:
                                                csvfile=open(temp_csv_filename, 'w')
                                                f = csv.writer(csvfile)
                                                
                                                re_sql = re.compile('(?s)(?:/\*(?P<header>.*)\*/|)(?P<body>.*)$')

                                                j = 0
                                                for sql in re.split('\r\n.*--delimiter--.*\r\n', job_data['sql']):
                                        
                                                        sql = sql.strip()
                
                                                        header = re_sql.match(sql).group('header')
                                                        sql = re_sql.match(sql).group('body')

                                                        sql = re.sub('--(>>|<<).*\\1--','', sql)

                                                        sql_stripped = sql.strip().strip('()').strip()	

                                                        if sql_stripped == '':
                                                                continue

                                                        if sql_stripped[:6].lower() == 'select':
                                                                save_result = True
                                                        elif sql_stripped[:4].lower() == 'with':
                                                                save_result = True
                                                        else:
                                                                save_result = False

                                                        cur = self.pgsql_conn.cursor()
                                                        cur.execute(sql)
                                                        
                                                        if save_result:	
                                                                colnames = [desc[0] for desc in cur.description]
                                                                colnames[-1] += '\x7f'

                                                                if j != 0:
                                                                        f.writerow('')

                                                                if 'skip_headers' in job_data and job_data['skip_headers']:
                                                                        pass
                                                                else:
                                                                        if header:
                                                                                f.writerow(['\x7f' + header.encode("utf-8")])

                                                                        f.writerow(list(colnames))

                                                                for i in cur.fetchall():
                                                                        f.writerow([unicode(x.decode('utf-8') if type(x) == str else '' if x is None else x).encode('utf-8') for x in i])

                                                                j = j + 1

                                                        cur.close()

                                                self.pgsql_conn.commit()

                                                csvfile.close()

                                                csv2xls(temp_csv_filename, temp_xls_filename, job_data['token'])

                                                os.rename(temp_csv_filename, csv_filename)
                                                os.rename(temp_xls_filename, xls_filename)

				send_email = True
				if 'send_empty_result' in job_data and job_data['send_empty_result'] == False:
					if len(csv2html(csv_filename, limit_per_table=-1)) == len(csv2html(csv_filename, limit_per_table=1)):
						send_email = False
			
				csvs_url = 'http://' + str(get_current_site(None)) + urlresolvers.reverse('reports.views.csvs', args=(job_data['token'],))
				calcv_url = 'http://' + str(get_current_site(None)) + urlresolvers.reverse('reports.views.calcv', args=(log.report.token.report.id,))
				if job_data['emails'] and send_email:
					MoguraEmail().send(job_data['title'], (job_data['message'] + '<br/><br/>' if 'message' in job_data else '') + '<a href="%s">%s</a><br/><br/>' % (csvs_url, calcv_url,) + codecs.decode(csv2html(csv_filename, limit_per_table = self.message_line_limit, merge_headers = True), 'utf-8'), job_data['emails'], xls_filename, job_data['title_csv'] + '.xlsx', 'jid=' + str(job.jid))

			except Exception, e:
				job.bury()

				error_message = unicode(traceback.format_exc(), errors='replace')[:65535]

				transaction.savepoint_rollback(log_savepoint)

				log.status = False
				log.error = error_message
				log.ts_finish = datetime.datetime.now()
				log.save()

				logger_url = 'http://' + str(get_current_site(None)) + urlresolvers.reverse('admin:logger_job_change', args=(log.id,))

				try:
					report_id = log.report.token.report.id
					report_url = 'http://' + str(get_current_site(None)) + urlresolvers.reverse('admin:reports_report_change', args=(report_id,))
				except:
					report_id = None

				if 'maintainers_emails' in job_data and job_data['maintainers_emails']:
					MoguraEmail().send(u'Ошибка выполнения отчета', u'<b>Отчет:</b><br/><br/>' + job_data['title'] + ' (id ' + (str(report_id) if report_id else u'не определен') + ')' + '<br/><br/>' + u'<b>Ошибка:</b><br/><br/>' + error_message + '</a>' + '<br/><br/>' + '<b>SQL:</b>' + '<br/>' + '<pre>' + job_data['sql'] + '</pre>' + '<br/><br/><a href="' + logger_url + '">' + logger_url + ('<br/><br/><a href="' + report_url + '">' + report_url + '</a>' if report_id else ''), job_data['maintainers_emails'])

				try:
					if 'error_emails' in job_data and job_data['error_emails'] and log.report_set.all()[:1].get().send_email:
						MoguraEmail().send(u'Ошибка выполнения отчета', u'<b>Отчет:</b><br/><br/>' + job_data['title'] + ' (id ' + (str(report_id) if report_id else u'не определен') + ')' + '<br/><br/>' + u'<b>Ошибка:</b><br/><br/>' + error_message, job_data['error_emails'])
				except:
					pass

				self.pgsql_conn.rollback()
			else:
				job.delete()

				log.status = True
				log.ts_finish = datetime.datetime.now()
				log.save()
			finally:
				self.pgsql_conn.close()


if __name__ == "__main__":
	if len(sys.argv) < 3:
		print "usage: python %s start|stop|restart daemon_token beanstalk_queue [beanstalk_queue ...]" % sys.argv[0]
		print "example: python %s start 1 ordinary" % sys.argv[0]
		sys.exit(2)
	
	daemon_token = sys.argv[2]

        try:
                beanstalk_queues = sys.argv[3:]
        except:
                beanstalk_queues = []

	daemon = MoguraDaemon('/var/run/mogurad-' + str(daemon_token) + '.pid', beanstalk_queues = beanstalk_queues)

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

