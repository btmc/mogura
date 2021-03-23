from django.conf.urls import include, url
from django.views.generic import DetailView, ListView
from reports.models import report
from django.contrib.auth.decorators import login_required
#from django.core.urlresolvers import reverse

# Uncomment the next two lines to enable the admin:

from reports.views import *

urlpatterns = [
    url(r'^calc/(?P<item_id>\d+)/?$', calc, name='reports.views.calc'),
    url(r'^(?P<item_id>\d+)/(?P<token>[0-9a-fA-F]{32})/?$', calcv, name='reports.views.calcv'),
    url(r'^csvs/(?P<token>[0-9a-fA-F]{32})/?$', csvs, name='reports.views.csvs'),
    url(r'^csve/(?P<token>[0-9a-fA-F]{32})/?$', csve, name='reports.views.csve'),
    url(r'^(?P<token>[0-9a-fA-F]{32})/?$', csvs, name='reports.views.csvs'),
    url(r'^csvd/(?P<token>[0-9a-fA-F]{32})/?$', csvd, name='reports.views.csvd'),
    url(r'^csva/(?P<token>[0-9a-fA-F]{32})/?$', csva, name='reports.views.csva'),
    url(r'^csvr/(?P<token>[0-9a-fA-F]{32})/?$', csvr, name='reports.views.csvr'),
    url(r'^sql/(?P<token>[0-9a-fA-F]{32})/?$', sql, name='reports.views.sql'),
    url(r'^csvr/(?P<token>[0-9a-fA-F]{32})/(?P<limit>[0-9]+)/?$', csvr, name='reports.views.csvr'),
    url(r'^csvr/(?P<token>[0-9a-fA-F]{32})/(?P<limit>[0-9]+)/(?P<offset>[0-9]+)/?$', csvr, name='reports.views.csvr'),
    url(r'^xlsd/(?P<token>[0-9a-fA-F]{32})/?$', xlsd, name='reports.views.xlsd'),
    url(r'^sendemail/(?P<token>[0-9a-fA-F]{32})/?$', sendemail, name='reports.views.sendemail'),
    url(r'^logout/?$', lgt, name='auth_logout'),
    url(r'^(?P<item_id>\d+)/?$', calcv, name='reports.views.calcv'),
    url(r'^$', start, name='reports.views.start'),
]
