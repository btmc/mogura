# Create your views here.
# coding: utf-8

#from django.template import Context, loader
from django import template
from django.http import HttpResponse
from reports.models import report
from reports import models

import logger

import beanstalkc, binascii, md5, json, os, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.admin import widgets

from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect

from csv2html import csv2html

from django.core.urlresolvers import reverse

from django import forms, http

from django.conf import settings 

import customModelFields
import customWidgets

from settings import *

from functools import wraps
from django.utils.decorators import available_attrs
from django.db.models import Q

import collections

import context

register = template.Library()

def sql_to_token(sql):
	return binascii.hexlify(md5.new(sql.encode('utf-8')).digest())

def authorization_required(function = None, redirect_to_start = False):
	def decorator(view_func):
		@wraps(view_func, assigned=available_attrs(view_func))
		def _wrapped_view(request, *args, **kwargs):
			try:
				if 'item_id' in kwargs:
					item_id = kwargs['item_id']
				elif 'token' in kwargs:
	 				item_id = report.objects.filter(token__pk=kwargs['token']).get().id 
				elif 'sql' in kwargs:
	 				item_id = report.objects.filter(token__pk=sql_to_token(kwargs['sql'])).get().id 

                                message='отчет не существует'
				report.objects.filter(pk=item_id).get()
                              
                                if request.user.is_staff == False: 
                                        message='отчет временно отключен' 
                                        report.objects.filter(pk=item_id, is_active=True).get()

                                        message='недостаточно прав для использования отчета'
                                        report.objects.filter(Q(users__pk=request.user.id) | Q(roles__euser__user=request.user.id), pk=item_id, is_active=True).distinct().get()

				return view_func(request, *args, **kwargs)	

			except report.DoesNotExist:
				if redirect_to_start:
					return start(request, message)
				else:
					return HttpResponse(status=401)

		return _wrapped_view

	if function:
		return decorator(function)

	return decorator	

def get_filepath(token):
	return str(settings.STORE_DIR + '/' + token[-4:-2] + '/' + token[-2:] + '/')

def get_csv_filename(token):
	return str(get_filepath(token) + token + '.csv')

def get_xls_filename(token):
	return str(get_filepath(token) + token + '.xlsx')

def form_class_factory(report_item, initial=None):
        class cls(forms.Form):
                base_fields = collections.OrderedDict()

                def clean(self):
                        super(cls, self).clean()

			if len(self._errors) > 0:
				raise ValidationError([])

                        groups = self._report.groups_evaluated()

			field_titles_list = []

                        if len(groups) > 0:
                                for group in groups.values():
                                        if len(group) == 0:
                                                continue

					field_titles = [] 
					for field in group.keys():
						field_titles.append(self[field].label) 	

                                        field_matches = False
                                        for field in group.keys():
                                                if field in self.cleaned_data and self.cleaned_data[field] not in (None, '', [], (), {}):
                                                        field_matches = True

                                        if not field_matches:
						#error_message = u'Нужно заполнить хотя бы одно из полей: ' + u', '.join(field_titles)
						error_message = u'vvv'
						for field in group.keys():
							#error_message = u'Нужно заполнить это поле или ' + u' или '.join(filter((self[field].label).__ne__, field_titles))

							#if field in self._errors:
							#	self._errors[field].append(error_message)
							#else:
							#	self._errors[field] = self.error_class([error_message])
							self._errors[field] = self.error_class([error_message])


						field_titles_list.append(field_titles)

			if len(field_titles_list) > 0:
				errors = []
				for field_titles in field_titles_list:
					 errors.append(u'Нужно заполнить хотя бы одно из полей: ' + ', '.join(field_titles))

				raise ValidationError(errors)

                        return self.cleaned_data

        cls._report = report_item

        dic = report_item.params_form_evaluated()
	
        if initial:
                for initial_field in initial.keys():
                        if initial_field in dic:
                                if not 'params' in dic[initial_field]:
                                        dic[initial_field]['params'] = {}
                                dic[initial_field]['params']['initial'] = initial[initial_field]

	for i in dic:
		if not 'params' in dic[i]:
			dic[i]['params'] = {}
		if not 'widget_params' in dic[i]:
			dic[i]['widget_params'] = {}

		if dic[i]['type'] == 'char':
			cls.base_fields[str(i)] = forms.CharField(**dic[i]['params'])
		elif dic[i]['type'] == 'int':
			cls.base_fields[str(i)] = forms.IntegerField(**dic[i]['params'])
		elif dic[i]['type'] == 'date':
			cls.base_fields[str(i)] = forms.DateField(**dic[i]['params'])
		elif dic[i]['type'] == 'datetime':
			cls.base_fields[str(i)] = forms.DateTimeField(**dic[i]['params'])
		elif dic[i]['type'] == 'boolean':
			cls.base_fields[str(i)] = forms.BooleanField(**dic[i]['params'])
		elif dic[i]['type'] == 'choice':
			cls.base_fields[str(i)] = customModelFields.ChoiceField(**dic[i]['params'])
		elif dic[i]['type'] == 'file':
			cls.base_fields[str(i)] = forms.FileField(**dic[i]['params'])
		elif dic[i]['type'] == 'ip':
			cls.base_fields[str(i)] = forms.GenericIPAddressField(**dic[i]['params'])

		elif dic[i]['type'] == 'choice_query':
			cls.base_fields[i] = customModelFields.ChoiceQueryField(**dic[i]['params'])
		elif dic[i]['type'] == 'multiple_choice':
			cls.base_fields[i] = customModelFields.MultipleChoiceField(**dic[i]['params'])
		elif dic[i]['type'] == 'multiple_choice_query':
			cls.base_fields[i] = customModelFields.MultipleChoiceQueryField(**dic[i]['params'])

		elif dic[i]['type'] == 'regexp':
			cls.base_fields[i] = customModelFields.RegexpField(**dic[i]['params'])

		elif dic[i]['type'] == 'char_list':
			cls.base_fields[i] = customModelFields.CharListField(**dic[i]['params'])
		elif dic[i]['type'] == 'regexp_list':
			cls.base_fields[i] = customModelFields.RegexpListField(**dic[i]['params'])

		elif dic[i]['type'] == 'day':
			cls.base_fields[i] = customModelFields.DayField(**dic[i]['params'])
		elif dic[i]['type'] == 'month':
			cls.base_fields[i] = customModelFields.MonthField(**dic[i]['params'])
		elif dic[i]['type'] == 'year':
			cls.base_fields[i] = customModelFields.YearField(**dic[i]['params'])

		try:
			if dic[i]['widget'] == 'AdminDateWidget':
				cls.base_fields[str(i)].widget = widgets.AdminDateWidget()
			elif dic[i]['widget'] == 'HiddenInput':
			        cls.base_fields[str(i)].widget = forms.HiddenInput()
			elif dic[i]['widget'] == 'TextInput':
				cls.base_fields[str(i)].widget = forms.TextInput(attrs = dic[i]['widget_params'])
                        elif dic[i]['widget'] == 'CodeMirrorSQLWidget':
                                cls.base_fields[str(i)].widget = customWidgets.CodeMirrorSQLWidget()
		except:
			pass	

                if 'hidden' in dic[i] and dic[i]['hidden'] == True:
                        if isinstance(cls.base_fields[i], forms.MultipleChoiceField):
                                cls.base_fields[str(i)].widget = forms.MultipleHiddenInput()
                        else:
                                cls.base_fields[str(i)].widget = forms.HiddenInput()

	return cls

class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
           if isinstance(obj, datetime.date):
                return str(obj) 
           return json.JSONEncoder.default(self, obj)

def lgt(request):
    logout(request)
    return redirect('/accounts/login')	

@login_required
def start(request, message='<= выберите отчет из списка слева'):
    return render(request, 'start.html', {'message': message},)

@csrf_exempt
@login_required
def sendemail(request, token):

    if request.method == 'POST':
        emails = request.body
    else:
        emails = request.user.email
        
    item = report.objects.filter(token__pk=token).get()
    token_item = models.token.objects.get(pk=token)

    dic = dict(json.loads(token_item.dictionary)) 

    b = beanstalkc.Connection(host=settings.BEANSTALK_HOST, port=settings.BEANSTALK_PORT)
    b.use(item.queue)

    job_item = logger.models.job.objects.get(pk=token_item.job_id)

    job_body = json.dumps({'sql': template.Template(item.sql_evaluated()).render(context.SafeContext(dic)), 'token': token, 'title': template.Template(item.title_email).render(context.SafeContext(dic)), 'title_csv': template.Template(item.title_csv).render(context.SafeContext(dic)), 'emails': emails, 'use_cache': True, 'message': template.Template(item.title).render(context.SafeContext(dic))})

    job_attrs = {}
    job_attrs['ttr'] = settings.BEANSTALK_TTR
    if item.job_priority != None:
	job_attrs['priority'] = item.job_priority + 1

    job_id = b.put(job_body, **job_attrs)

    log_item = job_item.report
    log_item.send_email = True
    log_item.save()

    mailing_job_body_item = logger.models.job_body(id = job_id, body = job_body)
    mailing_job_body_item.save()

    mailing_job_item = logger.models.job(id = job_id, ts_queue = datetime.datetime.now(), body = mailing_job_body_item, ttr = job_attrs['ttr'], priority = job_attrs['priority'] if 'priority' in job_attrs else None, report = log_item, queue=item.queue)
    mailing_job_item.save()
    mailing_job_item.blocking_jobs.add(job_item)

    return HttpResponse('Результат будет продублирован почтой.')

@login_required
@authorization_required(redirect_to_start=True)
def calc(request, item_id, sql = None, title = None, reset_cache = None):
    item = report.objects.get(pk=item_id)

    if sql == None:
    	sql = item.sql_evaluated()
    
    token = binascii.hexlify(md5.new(sql.encode('utf-8')).digest())
    token_item = models.token.objects.get(pk=token)
   
    dic = dict(json.loads(token_item.dictionary)) 

    if reset_cache == None:
    	reset_cache = item.reset_cache

    if reset_cache:
	try: 
		os.unlink(get_csv_filename(token))	
		os.unlink(get_xls_filename(token))	
	except:
		pass

    if os.path.isfile(get_csv_filename(token)) and os.path.getsize(get_csv_filename(token)) > 0:
	logger.models.report(user=request.user, token=token_item, reset_cache=False, is_cached=True, rc_exists=False).save()
	return csvs(request, token=token)
	
    if title == None:
        title = item.title

    title_csv = template.Template(item.title_csv).render(context.SafeContext(json.loads(token_item.dictionary)))
    title_email = template.Template(item.title_email).render(context.SafeContext(json.loads(token_item.dictionary)))

    b = beanstalkc.Connection(host=settings.BEANSTALK_HOST, port=settings.BEANSTALK_PORT)
    b.use(item.queue)

    #Check for race condition
    rc_exists = False

    if token_item.job_id:
	job = b.peek(token_item.job_id)
	if type(job) == beanstalkc.Job:
                try:
                        if job.stats()['state'] != 'buried':
                                rc_exists = True
                except beanstalkc.CommandFailed:
                        pass

    if not rc_exists:
	job_body = json.dumps({'sql': sql, 'token': token, 'title': title_email, 'title_csv': title_csv, 'emails': '', 'error_emails': request.user.email, 'message': title})
	job_attrs = {}
	job_attrs['ttr'] = settings.BEANSTALK_TTR
	if item.job_priority != None:
		job_attrs['priority'] = item.job_priority

    	token_item.job_id = b.put(job_body, **job_attrs)
	token_item.save()

    	logger_report = logger.models.report(user=request.user, token=token_item, reset_cache=reset_cache, is_cached=False, rc_exists=rc_exists)
	logger_report.save()

        job_body_item = logger.models.job_body(id = token_item.job_id, body = job_body)	
        job_body_item.save()

	logger.models.job(id = token_item.job_id, ts_queue = datetime.datetime.now(), body = job_body_item, ttr = job_attrs['ttr'], priority = job_attrs['priority'] if 'priority' in job_attrs else None, report = logger_report, queue = item.queue).save()

    return render(request, 'calc.html', {'token': token, 'item_id': item_id},)
    #return HttpResponse("Calculating sql: %s, token: %s" % (sql, token))

@login_required
@authorization_required(redirect_to_start=True)
def calcv(request, item_id, token=None):
    item = report.objects.get(pk=item_id)

    sql = item.sql_evaluated()
    title = item.title

    if sql:
	    if item.params_form:

		    if request.method == 'POST':
		        formClass = form_class_factory(item)
			form = formClass(request.POST, request.FILES, label_suffix = '')
			if form.is_valid():
			    for uploaded_file_field, uploaded_file in request.FILES.items():
				uploaded_file_hash = os.urandom(16).encode('hex')
				stored_uploaded_file_name = settings.UPLOAD_DIR + '/' + uploaded_file_hash
				with open(stored_uploaded_file_name, 'w') as stored_uploaded_file:
					for chunk in uploaded_file.chunks():
						stored_uploaded_file.write(chunk)

				form.cleaned_data[uploaded_file_field] = stored_uploaded_file_name	

                            form.cleaned_data.update({'token': '{{token}}'})

			    sql = template.Template(sql).render(context.SafeContext(form.cleaned_data))
			    token = binascii.hexlify(md5.new(sql.encode('utf-8')).digest())

                            form.cleaned_data.update({'token': token})

			    sql = template.Template(sql).render(context.SafeContext(form.cleaned_data))
			    token = binascii.hexlify(md5.new(sql.encode('utf-8')).digest())

			    title = template.Template(title).render(context.SafeContext(form.cleaned_data))
		 
			    try:	
				reset_cache = form.cleaned_data['reset_cache']
			    except:
				reset_cache = None

			    token_item = models.token.objects.get_or_create(token=token, report_id=item.id)[0]
			    token_item.dictionary=json.dumps({i:form.cleaned_data[i] for i in form.cleaned_data if i!='reset_cache'}, cls=CustomEncoder)
			    token_item.save()

			    return calc(request, item_id=item_id, sql=sql, title=title, reset_cache=reset_cache) 
		    else:
                        initial_dictionary = json.loads(models.token.objects.get(pk=token).dictionary) if token else {}
		        formClass = form_class_factory(item, initial=initial_dictionary)
			form = formClass(label_suffix = '')
		    #    raise Exception(formClass.__dict__)
		    return render(request, 'calcv.html', {'item_id': item_id, 'form': form, 'title': item.title_caption, 'title_header': item.title_menu_hier(), 'description': item.description, 'conflicts': item.conflicts_evaluated()},)
	    else:
		   token = binascii.hexlify(md5.new(sql.encode('utf-8')).digest())
		   models.token(token=token, report_id=item_id).save()

		   return calc(request, item_id=item_id)
    else:
	   return start(request)	    

def csvs(request, token):
    item = report.objects.get(token__pk=token)
    title = template.Template(item.title).render(context.SafeContext(json.loads(models.token.objects.get(pk=token).dictionary)))
    title_header = template.Template(item.title_email).render(context.SafeContext(json.loads(models.token.objects.get(pk=token).dictionary)))

    try:
	open(get_xls_filename(token))
	xls = True
    except:
	xls = False

    return render(request, 'csv.html', {'content': csv2html(get_csv_filename(token), limit = REPORT_CHUNK_SIZE), 'token': token, 'title': title, 'title_header': title_header, 'xls': xls, 'item_id': item.id, 'chunk_size': REPORT_CHUNK_SIZE},)   

def csve(request, token):
    item = report.objects.get(token__pk=token)
    title = template.Template(item.title).render(context.SafeContext(json.loads(models.token.objects.get(pk=token).dictionary)))
    title_header = template.Template(item.title_email).render(context.SafeContext(json.loads(models.token.objects.get(pk=token).dictionary)))

    try:
        open(get_xls_filename(token))
        xls = True
    except:
        xls = False

    return render(request, 'csv_embed.html', {'content': csv2html(get_csv_filename(token), limit = REPORT_CHUNK_SIZE), 'token': token, 'title': title, 'title_header': title_header, 'xls': xls, 'item_id': item.id, 'chunk_size': REPORT_CHUNK_SIZE},)

def csvd(request, token):
    response = HttpResponse(open(get_csv_filename(token)).read(), content_type='text/csv')
    report_item = report.objects.filter(token__pk=token).get()
    token_item = models.token.objects.get(pk=token)
    
    filename = template.Template(report_item.title_csv).render(context.SafeContext(json.loads(token_item.dictionary)))   
    response['Content-Disposition'] = 'attachment; filename="' + filename + '.csv"'
    
    return response

def csvr(request, token, offset = 0, limit = None):
    if limit:
	limit = int(limit) 

    return HttpResponse(csv2html(get_csv_filename(token), limit = limit, offset = int(offset)))

@login_required
@authorization_required
def csva(request, token):
    try:
        item = report.objects.filter(token__pk=token).get()
	response = csv2html(get_csv_filename(token), limit = REPORT_CHUNK_SIZE)
        title = template.Template(item.title).render(context.SafeContext(json.loads(models.token.objects.get(pk=token).dictionary)))
        title_header = template.Template(item.title_email).render(context.SafeContext(json.loads(models.token.objects.get(pk=token).dictionary)))

    	try:
		open(get_xls_filename(token))
		xls = True
    	except:
		xls = False
    except:
	return jobstate(request, token=token)

    return render(request, 'csva.html', {'content': response, 'item_id': item.id, 'token': token, 'title': title, 'title_header': title_header, 'xls': xls, 'chunk_size': REPORT_CHUNK_SIZE},)   

@login_required
@authorization_required
def sql(request, token):
    dictionary = json.loads(models.token.objects.get(pk=token).dictionary)
    
    return HttpResponse(template.Template('<pre>{% autoescape off %}{{sql}}{% endautoescape %}</pre>').render(context.SafeContext({'sql': template.Template(report.objects.get(token__pk=token).sql_evaluated()).render(context.SafeContext(dictionary))})))

@login_required
@authorization_required
def jobstate(request, token):
    try:
	b = beanstalkc.Connection(host=settings.BEANSTALK_HOST, port=settings.BEANSTALK_PORT)

	job_states = {'queued': 0, 'executed': 0, 'finished': 0,}

        for job_id in logger.models.job. \
                            objects.get (
                                            pk=models.token.objects.get(token=token,).job_id
                                        ).report.\
                                    job_set.all().values_list('id',flat=True):

		job = b.peek(job_id)

		if type(job) == beanstalkc.Job:
                        try:
                                job_state = job.stats()['state']

                                if job_state == 'ready':
                                        job_states['queued'] += 1
                                elif job_state == 'delayed':
                                        job_states['queued'] += 1
                                elif job_state == 'reserved':
                                        job_states['executed'] += 1
                                elif job_state == 'buried':
                                        return HttpResponse('<br/><font color="red">Ошибка обработки запроса</font>')
                                else:
                                        return HttpResponse('<br/>Неизвестный статус обработки запроса')
                        except beanstalkc.CommandFailed:
                                job_states['finished'] += 1 
		else:
			job_states['finished'] += 1

	return HttpResponse('<br/>Запрос обрабатывается (подзадач в очереди: <font color="darkblue"><b>%(queued)s</b></font>, обрабатывается: <font color="darkgoldenrod"><b>%(executed)s</b></font>, выполнено: <font color="darkgreen"><b>%(finished)s</b></font>)' % job_states)

    except:
	return HttpResponse('<br/><font color="red">Ошибка получения статуса</font>')	
	
def xlsd(request, token):
    response = HttpResponse(open(get_xls_filename(token)).read(), content_type='application/octet-stream')
    report_item = report.objects.filter(token__pk=token).get()
    token_item = models.token.objects.get(pk=token)
    
    filename = template.Template(report_item.title_csv).render(context.SafeContext(json.loads(token_item.dictionary)))   
    response['Content-Disposition'] = 'attachment; filename="' + filename + '.xlsx"'
    
    return response
