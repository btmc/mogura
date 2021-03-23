# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mptt.models import MPTTModel, TreeForeignKey

import json, re

from datetime import *

import collections

import exec_helpers as eh

# Create your models here.

class role(models.Model):
	def __unicode__(self):
		return self.title

	title = models.CharField(max_length=256)

class queue(models.Model):
	def __unicode__(self):
		return self.title

	title = models.CharField(max_length=32)

class report(MPTTModel):

 	class MPTTMeta:
    		order_insertion_by = ['priority',]

        params_reset_cache = dict(json.loads("""
{
	"reset_cache":  {
				"type": "boolean",
				"params":               {
								"label": "сбросить кеш",
								"required": false
							}
			}
}
"""))

	params_send_email = dict(json.loads("""
{
	"send_email":  {
				"type": "boolean",
				"params":               {
								"label": "отправить почтой",
								"required": false
							}
			}
}
"""))

	def __unicode__(self):
		return '%s [%s]' % (self.title_menu, self.pk,)

	def sql_short(self):
		return self.sql[:10]

	def title_menu_hier(self):
		if self.parent_id != None:
			return report.objects.get(pk=self.parent_id).title_menu_hier() + ' - ' + self.title_menu
		else:
			return self.title_menu

	def save(self, *args, **kwargs):
		if not self.title_menu:
			self.title_menu = self.title
		if not self.title_csv:
			self.title_csv = self.title
		if not self.title_email:
			self.title_email = self.title
		if not self.title_caption:
			self.title_caption = self.title_menu

		super(report, self).save(*args, **kwargs)

        def sql_evaluated(self):
                def subreport_query_block_evaluated(match):
                    return   '-->> %(block_id)s >>--%(block_query)s--<< %(block_id)s <<--' % subreport_query_block.groupdict()
                
                sql = self.sql
                for subreport in self.subreports.all():
                        override_params = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(report_subreports.objects.get(report=self.id, subreport=subreport.id).params_form)

                        subreport_sql = subreport.sql_evaluated()
                        for i in override_params:
                                if isinstance(override_params[i], collections.Mapping):
                                        if 'map_to' in override_params[i]:
                                                subreport_sql = re.sub('(?P<tag_pre>\{%%[^%%}]*)%s(?P<tag_post>[^%%}]*%%\})' % (i,), '\g<tag_pre>%s\g<tag_post>' % (override_params[i]['map_to'],), subreport_sql)
                                                subreport_sql = re.sub('(?P<tag_pre>\{\{[^}]*)%s(?P<tag_post>[^}]*\}\})' % (i,), '\g<tag_pre>%s\g<tag_post>' % (override_params[i]['map_to'],), subreport_sql) 

                        sql = re.sub('--\|\s*%s\s*\|--' % (subreport.id,), lambda m: subreport_sql, sql)

                        sql = re.sub('(?i)--\|\|\s*%s:(?P<block_id>[a-z0-9-_]+)\s*\|\|--' % (subreport.id,), '-->> \g<block_id> >>--%s--<< \g<block_id> <<--' % ('\n',), sql)

                        for subreport_query_block in re.finditer('(?ism)-->>\s*(?P<block_id>[a-z0-9-_]+)\s*>>--(?P<block_query>.*)--<<\s*\\1\s*<<--', subreport_sql):
                                sql = re.sub    ( \
                                                        '(?ism)-->>\s*%(block_id)s\s*>>--.*?--<<\s*%(block_id)s\s*<<--' % subreport_query_block.groupdict(), \
                                                        subreport_query_block_evaluated, \
                                                        sql \
                                                )

                return sql

        def reset_cache_evaluated(self):
                reset_cache = self.reset_cache
                for subreport in self.subreports.all():
                        reset_cache = reset_cache or subreport.reset_cache

                return reset_cache

	def params_form_evaluated(self):
                res=self.params_form_substituted()
                for subreport in self.subreports.order_by('dependencies__order'):
                        subreport_params = subreport.params_form_evaluated()
                        override_params = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(report_subreports.objects.get(report=self.id, subreport=subreport.id).params_form)

                        for i in override_params:
                                if i in subreport_params:
                                        if not 'params' in subreport_params[i]:
                                                subreport_params[i]['params'] = {}

                                        if isinstance(override_params[i], collections.Mapping):
                                                if 'initial' in override_params[i]:
                                                        subreport_params[i]['params']['initial'] = override_params[i]['initial']                         
                                                if 'hidden' in override_params[i]:
                                                        subreport_params[i]['hidden'] = override_params[i]['hidden']
                                        else:
                                                subreport_params[i]['params']['initial'] = override_params[i]

                        subreport_params_mapped = collections.OrderedDict()
                                                
                        for i in subreport_params:

                                map_key = i
                                if i in override_params and isinstance(override_params[i], collections.Mapping):
                                        if 'map_to' in override_params[i]:
                                                map_key = override_params[i]['map_to']

                                subreport_params_mapped[map_key] = subreport_params[i]
                        
                        res.update(subreport_params_mapped)

                res.update(self.params_form_substituted())

                if 'reset_cache' in res:
                        del res['reset_cache']

                if not self.reset_cache_evaluated():
                        res.update(self.params_reset_cache)

                return res
        
        def params_form_substituted(self):                
		try:
			res = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(self.params_form)

			def _(i, ns):
				if 'initial' in res[i]['params']:
					if type(res[i]['params']['initial']) == str or type(res[i]['params']['initial']) == unicode:
						if res[i]['params']['initial'].find('exec ') == 0:
							res[i]['params']['initial'] =  res[i]['params']['initial'].replace('exec ', 'res[i][\'params\'][\'initial\'] = ', 1)
							exec res[i]['params']['initial'] in globals(), dict(ns.items() + locals().items())

					x = res[i]['params']['initial']
                                        return unicode(x.decode('utf-8') if type(x) == str else '' if x is None else x).encode('utf-8')

			for i in res:
				try:
					if 'params' in res[i]: 
						_(i, locals())

						#make a list from choices dictionary
						if 'choices' in res[i]['params']:
                                                        if isinstance(res[i]['params']['choices'], collections.Mapping):
								res[i]['params']['choices'] = res[i]['params']['choices'].items()
				except:
					raise 

			return res
		except:
                        raise

	def conflicts_evaluated(self):
                def parse_dict(src, res=collections.defaultdict(dict), key=[]):
                        if isinstance(src, dict) and len(src) > 0:
                                for k,v in src.iteritems():
                                        res = parse_dict(v, res, key)
                                        res = parse_dict(v, res, key + [k])
                        else:
                                if len(key) > 1:
                                        if isinstance(src, list):
                                                forward = src[0] if len(src) > 0 else ''
                                                reverse = src[-1] if len(src) > 0 else ''
                                        elif isinstance(src, dict):
                                                forward = reverse = ''
                                        else:
                                                forward = reverse = src

                                        if forward != None:
                                                res[key[0]].update({key[-1]:forward})
                                        if reverse != None:
                                                res[key[-1]].update({key[0]:reverse})
  
                        return res

                res = {}
                for subreport in self.subreports.order_by('dependencies__order'):
                        res.update(subreport.conflicts_evaluated())

		res.update(dict(parse_dict(json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(self.conflicts if self.conflicts else '{}'))))

                return res

	def groups_evaluated(self):
                res = {}
                for subreport in self.subreports.order_by('dependencies__order'):
                        res.update(subreport.groups_evaluated())

		res.update(json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(self.groups if self.groups else '{}'))

                return res

	def is_hidden(self):
		try:
			return self.parent.is_hidden() or not self.is_active
		except:
			return not self.is_active

	def path_to_root(self):
		try:
			return self.parent.path_to_root() + [self] 
		except:
			return [self]

	priority = models.IntegerField(default=1)
	queue = models.ForeignKey(queue, blank=False, null=False)
	is_active = models.BooleanField(default=True)
	job_priority = models.IntegerField(blank=True, null=True)
	title_menu = models.TextField(blank=True)
	title_csv = models.TextField(blank=True)
	title_email = models.TextField(blank=True)
	title = models.TextField()
	title_caption = models.TextField(blank=True)
	sql = models.TextField(blank=True)
	params_form = models.TextField(blank=True, null=True)
	conflicts = models.TextField(blank=True, null=True)
	groups = models.TextField(blank=True, null=True)
	users = models.ManyToManyField(User)
	reset_cache = models.BooleanField(default=True)
	parent = TreeForeignKey('self', blank=True, null=True)
	roles = models.ManyToManyField(role)
	description = models.TextField(blank=True, null=True)
	xls_charts_udf = models.TextField(blank=True, null=True)
        subreports = models.ManyToManyField('self', through='report_subreports', through_fields=('report', 'subreport'), related_name='dependent_reports', symmetrical=False)

class report_subreports(models.Model):
        class Meta:
                unique_together = ('report', 'subreport',)
                verbose_name = 'Subreport'

        subreport = TreeForeignKey(report, related_name='dependencies', on_delete=models.PROTECT)
        report = models.ForeignKey(report, related_name='+')
        order  = models.IntegerField(blank=True, null=True)
        params_form = models.TextField(blank=True, null=True, verbose_name='Custom initial values for params')

class token(models.Model):
	def __unicode__(self):
		return self.token

	token = models.CharField(max_length=32, primary_key=True)
	report = models.ForeignKey(report)
	dictionary = models.TextField(blank=True, default='{}')
	job_id = models.IntegerField(null=True)

	def direct_url(self):
		return reverse('reports.views.csvs', kwargs={'token':self.token})	

class euser(models.Model):
	def __unicode__(self):
		return self.user.username 

	def title(self):
		return self.user.username

	user = models.OneToOneField(User)
	roles = models.ManyToManyField(role)

