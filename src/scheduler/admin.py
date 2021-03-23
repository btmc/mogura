# coding: utf-8

from scheduler.models import schedule, chain
from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin
from reports.customWidgets import JSONEditorWidget, CodeMirrorSQLWidget
from django import forms
from django.contrib.auth.models import User

class chainInline(admin.StackedInline):
    def formfield(self, db_field, request, **kwargs):
		if db_field.name == 'order':
			raise Exception('here')
			kwargs['initial'] = '99'

		return super(chainInline, self).formfield(db_field, request, **kwargs)	

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == 'order':
			raise Exception('here2')
			kwargs['initial'] = self.model.schedule
			kwargs['initial'] = 'test'
			return db_field.formfield(**kwargs)

		return super(chainInline, self).formfield_for_foreignkey(db_field, request, **kwargs)	

    model = chain
    extra = 0

class scheduleForm (forms.ModelForm):
    params_form = forms.CharField(max_length=65535, required=False, widget=JSONEditorWidget(), label='Custom params')
    maintainers = forms.ModelMultipleChoiceField(required=False, queryset = User.objects.all(), widget=admin.widgets.FilteredSelectMultiple("maintainers", is_stacked=False))
    users = forms.ModelMultipleChoiceField(required=False, queryset = User.objects.all(), widget=admin.widgets.FilteredSelectMultiple("users", is_stacked=False))
    precheck_sql = forms.CharField(max_length=65535, required=False, widget=CodeMirrorSQLWidget())

class scheduleAdmin (CompareVersionAdmin):
    def enable(self, request, queryset):
        queryset.update(is_active = True)

    def disable(self, request, queryset):
        queryset.update(is_active = False)

    def get_actions(self, request):
	actions = super(scheduleAdmin, self).get_actions(request)

	try:
		if 'is_active__exact' in request.GET:
			if request.GET['is_active__exact'] == '1':
				del actions['enable']
			if request.GET['is_active__exact'] == '0':
				del actions['disable']
	except:
		pass

	return actions

    list_display = ('menu_title', 'last_time_f', 'modifier', 'is_active', 'queue', 'users_list', 'emails', 'params_form',)
    list_filter = ('is_active', 'modifier', 'queue',)
    ordering = ('modifier', '-last_time',)
    actions = [enable, disable,]
    save_as = True
    inlines = [ chainInline, ]
    form = scheduleForm

admin.site.register(schedule, scheduleAdmin)
