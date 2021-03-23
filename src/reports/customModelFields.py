 # -*- coding: utf-8 -*-

"""
Custom model fields
"""

import re, psycopg2
from django.core.exceptions import ValidationError
from django import forms

from datetime import *

from settings import *

import customWidgets

class ChoiceField(forms.ChoiceField):
	def __init__(self, *args, **kwargs):
                if 'initial' in kwargs:
                        for choice in kwargs['choices']:
                                if kwargs['initial'] == choice[0]:
                                        kwargs['initial'] = choice[0]
                                        break
                        
		super(ChoiceField, self).__init__(*args, **kwargs)	

class QueryFieldMixin(forms.Field):
	def __init__(self, *args, **kwargs):
		if 'query' not in kwargs:
			raise Exception('Query parameter is missing.')

		pgsql_conn = psycopg2.connect(PGSQL_DSN)
                cur = pgsql_conn.cursor()
                psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, cur)
                cur.execute(kwargs['query'])	

		if 'choices' not in kwargs:
			kwargs['choices'] = list()

		for i in cur.fetchall():
                	kwargs['choices'].append(list(i))
		cur.close()
		
		del kwargs['query']

		super(QueryFieldMixin, self).__init__(*args, **kwargs)	

class ChoiceQueryField(QueryFieldMixin, ChoiceField):
        pass

class MultipleChoiceField(forms.MultipleChoiceField):
	def __init__(self, *args, **kwargs):
		if 'enclosed_by' in kwargs:
			self.item_template = kwargs['enclosed_by'] + "%s" + kwargs['enclosed_by']
			del kwargs['enclosed_by']
		else:
			self.item_template = "%s"

		if 'enclosed_by_template' in kwargs:
			self.item_template = kwargs['enclosed_by_template']
			del kwargs['enclosed_by_template']

		if 'delimited_by' in kwargs:
			self.delimiter = kwargs['delimited_by']
			del kwargs['delimited_by']
		else:
			self.delimiter = ','

                if 'initial' in kwargs:
                        if not isinstance(kwargs['initial'], basestring):
                                kwargs['initial'] = str(kwargs['initial'])

                        initial_list = []
                        for line in re.split(self.delimiter, kwargs['initial']):
                                initial_list += [re.match(self.item_template % '(.*)', line).group(1)]

                        choice_list = []
                        for initial_item in initial_list:
                                for choice in kwargs['choices']:
                                        if str(initial_item) == str(choice[0]):
                                                choice_list += [choice[0]]

                        kwargs['initial'] = choice_list 

                self.widget = forms.SelectMultiple(attrs={'size': min(len(kwargs['choices']), 20)})

		super(MultipleChoiceField, self).__init__(*args, **kwargs)	

	def clean(self, value):
		self.cleared_data = []

		if self.required and not value:
                        raise ValidationError(self.error_messages['required'])

                try:
                        i = 0
                        for item in value:
                                i += 1
                                self.cleared_data.append(self.item_template % forms.CharField(required=False).clean(item))	
                except:
                        raise ValidationError(self.error_messages['invalid'] + ' (' + str(i) + u'-я строка)')

		return self.delimiter.join(self.cleared_data)

class MultipleChoiceQueryField(QueryFieldMixin, MultipleChoiceField):
	pass

class ListField(forms.Field):
	def __init__(self, *args, **kwargs):
		args = list(args)

		if not 'error_messages' in kwargs:
			kwargs['error_messages'] = {} 
		if 'required' not in kwargs['error_messages']:
			kwargs['error_messages']['required'] = u"Это поле обязательно нужно заполнить"

		if 'enclosed_by' in kwargs:
			self.item_template = kwargs['enclosed_by'] + "%s" + kwargs['enclosed_by']
			del kwargs['enclosed_by']
		else:
			self.item_template = "%s"

		if 'enclosed_by_template' in kwargs:
			self.item_template = kwargs['enclosed_by_template']
			del kwargs['enclosed_by_template']

		if 'delimited_by' in kwargs:
			self.delimiter = kwargs['delimited_by']
			del kwargs['delimited_by']
		else:
			self.delimiter = ','

                if 'initial' in kwargs and kwargs['initial']:
                        initial_view = []
                                 
                        for line in re.split(self.delimiter, kwargs['initial']):
                                initial_view += [re.match(self.item_template % '(.*)', line).group(1)]

                        kwargs['initial'] = '\n'.join(initial_view)

		if not issubclass(args[0], forms.Field):
			raise TypeError('Field class is not a subclass of forms.Field')
		else:
			if 'field_params' not in kwargs:
				kwargs['field_params'] = {}

			self.field_class = args.pop(0)(**kwargs.pop('field_params'))

		self.widget = forms.Textarea(attrs={'cols': 64, 'rows': 15})

		super(ListField, self).__init__(*args, **kwargs)	

	def clean(self, value):
		if not self.required and not value:
			return None 
		
		if not value:
			raise ValidationError(self.error_messages['required'])

		self.cleared_data = []
		try:
			i = 0
			for item in iter(value.splitlines()):
				i += 1
				self.cleared_data.append(self.item_template % self.field_class.clean(item))	
		except ValidationError as e:
			raise ValidationError(e.messages[0] + ' (' + str(i) + u'-я строка)')

		return self.delimiter.join(self.cleared_data)

class RegexpListField(ListField):
	def __init__(self, *args, **kwargs):
		if not 'label' in kwargs:
			kwargs['label'] = u"список строк"

		if 'enclosed_by' not in kwargs:
			kwargs['enclosed_by'] = "'"

		super(RegexpListField, self).__init__(RegexpField, *args, **kwargs)

CharListField = RegexpListField

class RegexpField(forms.CharField):
	widget = forms.TextInput(attrs = {'size': '64'})

	class regexp(object):
		def __init__(self, *args):
			try:
				self.expand = args[0]['expand']
			except:
				self.expand = '\g<1>'

			try:
				self.regexp = args[0]['regexp']
			except:
				self.regexp = args[0]

			
	def __init__(self, *args, **kwargs):
		if 'regexp_list' in kwargs:
			self.regexp_list = [RegexpField.regexp(r) for r in kwargs.pop('regexp_list')]
		else:
			self.regexp_list = [RegexpField.regexp('^(.*)$')]
		
		if 'error_messages' not in kwargs:
			kwargs['error_messages'] = {} 

		if 'invalid' not in kwargs['error_messages']:
			kwargs['error_messages']['invalid'] = u"Значение должно удовлетворять одному из регулярных выражений: %s" % ' , '.join([r.regexp for r in self.regexp_list])
		if 'required' not in kwargs['error_messages']:
			kwargs['error_messages']['required'] = u"Это поле обязательно нужно заполнить"

		super(RegexpField, self).__init__(*args, **kwargs)

	def clean(self, value):
		value = super(RegexpField, self).clean(value)

		for regexp in self.regexp_list:
			try:
				return re.search(regexp.regexp, value).expand(regexp.expand)	
			except:
				pass		

		if self.required:
			raise ValidationError(self.error_messages['invalid'])

class DayField(forms.DateField):
	def __init__(self, *args, **kwargs):
		if not 'error_messages' in kwargs:
			kwargs['error_messages'] = {} 

		if 'invalid' not in kwargs['error_messages']:
			kwargs['error_messages']['invalid'] = u"Значение должно быть датой в формате гггг-мм-дд"
		if 'required' not in kwargs['error_messages']:
			kwargs['error_messages']['required'] = u"Это поле обязательно нужно заполнить"
		
		if not 'help_text' in kwargs:
			kwargs['help_text'] = u"(гггг-мм-дд)"

		if not 'initial' in kwargs:
			kwargs['initial'] = (date.today() - timedelta(1)).strftime('%Y-%m-%d')
	
		if not 'widget' in kwargs:
			kwargs['widget'] = customWidgets.DayWidget() 

		super(DayField, self).__init__(*args, **kwargs)

class MonthField(forms.DateField):
	def __init__(self, *args, **kwargs):
		if not 'error_messages' in kwargs:
			kwargs['error_messages'] = {} 

		if 'invalid' not in kwargs['error_messages']:
			kwargs['error_messages']['invalid'] = u"Значение должно быть месяцем в формате гггг-мм"
		if 'required' not in kwargs['error_messages']:
			kwargs['error_messages']['required'] = u"Это поле обязательно нужно заполнить"
		
		if not 'help_text' in kwargs:
			kwargs['help_text'] = u"(гггг-мм)"

		if not 'label' in kwargs:
			kwargs['label'] = u"месяц"

		if not 'input_formats' in kwargs:
			kwargs['input_formats'] = ["%Y-%m"]

		if not 'initial' in kwargs:
			kwargs['initial'] = (date.today() - timedelta(28)).strftime('%Y-%m')

		if not 'widget' in kwargs:
			kwargs['widget'] = customWidgets.MonthWidget() 

		super(MonthField, self).__init__(*args, **kwargs)

	def clean(self, value):
		result = super(MonthField, self).clean(value)

		if type(result) == date:
			return result.strftime('%Y-%m')
		else:
			return result

class YearField(forms.DateField):
	def __init__(self, *args, **kwargs):
		if not 'error_messages' in kwargs:
			kwargs['error_messages'] = {} 

		if 'invalid' not in kwargs['error_messages']:
			kwargs['error_messages']['invalid'] = u"Значение должно быть годом (4 цифры)"
		if 'required' not in kwargs['error_messages']:
			kwargs['error_messages']['required'] = u"Это поле обязательно нужно заполнить"
		
		if not 'help_text' in kwargs:
			kwargs['help_text'] = u"(гггг)"

		if not 'label' in kwargs:
			kwargs['label'] = u"год"

		if not 'input_formats' in kwargs:
			kwargs['input_formats'] = ["%Y"]

		if not 'initial' in kwargs:
			kwargs['initial'] = (date.today() - timedelta(365)).strftime('%Y')

		if not 'widget' in kwargs:
			kwargs['widget'] = customWidgets.YearWidget() 

		super(YearField, self).__init__(*args, **kwargs)

	def clean(self, value):
		result = super(YearField, self).clean(value)

		if type(result) == date:
			return result.strftime('%Y')
		else:
			return result
