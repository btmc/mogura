from django.conf.urls import include, url
import settings

from django.contrib import admin
admin.autodiscover()

import django.contrib.auth.views
import django.views.static

urlpatterns = [ 
    url(r'^accounts/login/?$', django.contrib.auth.views.login, kwargs={'template_name': 'login.html'}, name='django.contrib.auth.views.login'),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^static/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.STATIC_ROOT}, name='django.views.static.serve',),
    
    url(r'^', include('reports.urls')),
]
