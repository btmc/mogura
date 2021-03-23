import re
import sys
import cStringIO
import datetime
import psycopg2
import string

from django import template
from django.db.models import Q

from reports.models import report

from settings import *

import context

register = template.Library()

@register.inclusion_tag('templatetags/menu.html')
def menu(user, item_id):
        if user.id:
                return {'menu_list': report.objects.filter(Q(users__pk=user.id) | Q(roles__euser__user=user.id), is_active=True).order_by('priority').order_by('title').distinct(), 'item_id': int(item_id) if item_id != '' else 0}

@register.inclusion_tag('templatetags/header.html')
def header(user): return {'user': user}

@register.inclusion_tag('templatetags/conflicts.html')
def conflicts(conflicts): return {'conflicts': conflicts}

@register.filter
@template.defaultfilters.stringfilter
def split(value_list, delimiter=','): return [x for x in value_list.split(delimiter)]

@register.filter
@template.defaultfilters.stringfilter
def render_template(value): return template.Template(value).render(context.SafeContext({}))

@register.filter
def nth(item_list, arg):
        return item_list[arg]

#https://djangosnippets.org/snippets/60/
@register.filter
@template.defaultfilters.stringfilter
def replace ( string, args ):
    search  = args.split(args[0])[1]
    replace = args.split(args[0])[2]

    return re.sub( search, replace, string )

class AssignNode(template.Node):
    def __init__(self, *args):
        (self.nodelist, self.output) = args

    def render(self, context):
        context[self.output] = self.nodelist.render(context).strip()

        return ''

@register.tag()
def assign (parser, token):
    nodelist = parser.parse(('endassign'),)
    parser.delete_first_token()

    return AssignNode(nodelist, token.split_contents()[1])

class QueryNode(template.Node):
	def __init__(self, nodelist, output):
		self.nodelist = nodelist
                self.output = output

                self.pgsql_conn = psycopg2.connect(PGSQL_DSN)

	def render(self, context):
		sql = self.nodelist.render(context)

                cur = self.pgsql_conn.cursor()
                cur.execute(sql)

                result = []
                try:
                    for i in cur.fetchall():
                            result += [list(i)]
                except  psycopg2.ProgrammingError:
                    pass

                self.pgsql_conn.commit()

                context[self.output] = result

                return ''

@register.tag()
def query (parser, token):
	nodelist = parser.parse(('endquery'),)
	parser.delete_first_token()

	return QueryNode(nodelist, token.split_contents()[1])

class PythonNode(template.Node):
	def __init__(self, nodelist):
		self.nodelist = nodelist

	def render(self, context):
		code = self.nodelist.render(context)
		stdout = sys.stdout = cStringIO.StringIO()
		exec code
		sys.stdout = sys.__stdout__
		return stdout.getvalue() 

@register.tag()
def python (parser, token):
	nodelist = parser.parse(('endpython'),)
	parser.delete_first_token()

	return PythonNode(nodelist)

class ItemNode(template.Node):
	def __init__(self, item_id):
		self.item_id = item_id

	def render(self, context):
		return template.Template(report.objects.get(pk=self.item_id).sql).render(context)

@register.tag()
def item(parser, token):
	return ItemNode(token.split_contents()[1])

class MoguraMLNode(template.Node):
        def __init__(self, nodelist, tag, params):
                self.tag = 'mogura:html:%s' % tag
                self.params = str(params).translate(string.maketrans('&"', '#`'))
                self.nodelist = nodelist

        def render(self, context):
                if self.nodelist:
                        tag_contents = self.nodelist.render(context)

                        return '[~%(tag)s%(tilde)s%(params)s~]%(contents)s[~/%(tag)s~]' % {'tag': self.tag, 'params': self.params, 'contents': tag_contents, 'tilde': '~' if len(self.params) > 0 else ''}
                else:
                        return '[~%(tag)s%(tilde)s%(params)s~]' % {'tag': self.tag, 'params': self.params, 'tilde': '~' if len(self.params) > 0 else ''}

@register.tag()
def mmlbegin(parser, token):
        nodelist = parser.parse(('mmlend'),)
        parser.delete_first_token()

        params = ' '.join(token.split_contents()[2:])

        return MoguraMLNode(nodelist, token.split_contents()[1], params)

@register.tag()
def mml(parser, token):
        params = ' '.join(token.split_contents()[2:])

        return MoguraMLNode(None, token.split_contents()[1], params)

@register.simple_tag()
def daydiff(day_from, day_to):
	return (datetime.date(*map(int, str(day_to).split('-'))) - datetime.date(*map(int, str(day_from).split('-')))).days + 1

@register.simple_tag()
def monthdiff(day_from, day_to):
	day_from = datetime.date(*map(int, str(day_from).split('-')))
	day_to = datetime.date(*map(int, str(day_to).split('-')))

	return (day_to.year - day_from.year) * 12 + day_to.month - day_from.month + 1

@register.simple_tag()
def daylist(day_from, day_to):
        try:
                n = daydiff(day_from, day_to)
        except:
                n = int(day_to)

        days = []
        for i in range(0, n):
               days += ['\'%s\'' % ((datetime.date(*map(int, str(day_from).split('-'))) + datetime.timedelta(i)).isoformat(),)]

	return ','.join(days) 
