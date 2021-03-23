# coding: utf-8

from reports.models import *
from django.contrib import admin
from django import forms
from django.db import models
from django.contrib.auth.models import User
from mptt.admin import MPTTModelAdmin
from customWidgets import JSONEditorWidget, CodeMirrorSQLWidget, CodeMirrorHTMLWidget, CodeMirrorPythonWidget
from reversion_compare.admin import CompareVersionAdmin
import json
import itertools
import feincms.admin.tree_editor

class reportForm (forms.ModelForm):

	class Meta:
		exclude = ['job_id', 'priority']

        queue = forms.ModelChoiceField(queryset=queue.objects.all(), empty_label=None)
        title_menu = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'size': 200}))
        title_csv = forms.CharField(max_length=65535, required=False, widget=forms.TextInput(attrs={'size': 200}))
        title_email = forms.CharField(max_length=65535, required=False, widget=forms.TextInput(attrs={'size': 200}))
	title = forms.CharField(max_length=65535, widget=CodeMirrorHTMLWidget())
	title_caption = forms.CharField(max_length=65535, required=False, widget=CodeMirrorHTMLWidget())
        sql = forms.CharField(max_length=65535, required=False, widget=CodeMirrorSQLWidget())
        params_form = forms.CharField(max_length=65535, required=False, widget=JSONEditorWidget())
        conflicts = forms.CharField(max_length=65535, required=False, widget=JSONEditorWidget())
        groups = forms.CharField(max_length=65535, required=False, widget=JSONEditorWidget())
        users = forms.ModelMultipleChoiceField(required=False, queryset = User.objects.all(), widget=admin.widgets.FilteredSelectMultiple("users", is_stacked=False))
	reset_cache = forms.BooleanField(required=False, label='Принудительно сбрасывать кеш')
	roles = forms.ModelMultipleChoiceField(required=False, queryset = role.objects.all(), widget=admin.widgets.FilteredSelectMultiple("roles", is_stacked=False))
	description = forms.CharField(max_length=65535, required=False, widget=CodeMirrorHTMLWidget())
	xls_charts_udf = forms.CharField(max_length=65535, required=False, widget=CodeMirrorPythonWidget())

class euserForm(forms.ModelForm):
	roles = forms.ModelMultipleChoiceField(required=False, queryset = role.objects.all(), widget=admin.widgets.FilteredSelectMultiple("roles", is_stacked=False))

class subreportForm(forms.ModelForm):
        params_form = forms.CharField(max_length=65535, required=False, widget=JSONEditorWidget())

class subreportInline(admin.StackedInline):
        form = subreportForm
        model = report_subreports
        fk_name = 'report'
        extra = 0

class reportAdmin (feincms.admin.tree_editor.TreeEditor, CompareVersionAdmin):
	class hiddenFilter (admin.SimpleListFilter):
		title = 'is_hidden'
		parameter_name = 'is_hidden'

		def lookups(self, request, report):
			return	(
					(0, 'All',),
					(None, 'False',),
					(1, 'True',),
				)

		def choices(self, cl):
			for lookup, title in self.lookup_choices:
				yield 	{
						'selected': self.value() == lookup,
						'query_string': cl.get_query_string({self.parameter_name: lookup,}, []),
						'display': title,
					}

		def queryset(self, request, queryset):
			if self.value() == '1':
				return queryset.filter(id__in=itertools.chain(*[[y.id for y in x.path_to_root()] for x in queryset if x.is_hidden()]))
			if self.value() == '0':
				return queryset
			else:
				return queryset.filter(id__in=itertools.chain(*[[y.id for y in x.path_to_root()] for x in queryset if not x.is_hidden()]))

	def enable(self, request, queryset):
		queryset.update(is_active = True)

	def disable(self, request, queryset):
		queryset.update(is_active = False)

	list_filter = (hiddenFilter, 'roles', 'users',)
        list_per_page = 10000
	actions = [enable, disable,]
        inlines = [subreportInline,]
    	form = reportForm
	save_as = True

class roleAdmin (CompareVersionAdmin):
	list_display = ('title',)

class euserAdmin (CompareVersionAdmin):
	list_display = ('title',)
	form = euserForm

class tokenAdmin (admin.ModelAdmin):
	def has_add_permission(self, request):
                return False

        def has_delete_permission(self, request, obj=None):
                return False

	actions = None

	list_display = ('token', 'job_id', 'dictionary')
	readonly_fields = ('token', 'dictionary', 'job_id')
	exclude = ('report',)
	list_filter = ('report',)

class queueAdmin (CompareVersionAdmin):
	list_display = ('title',)

admin.site.register(report, reportAdmin)
admin.site.register(role, roleAdmin)
admin.site.register(euser, euserAdmin)
admin.site.register(token, tokenAdmin)
admin.site.register(queue, queueAdmin)
