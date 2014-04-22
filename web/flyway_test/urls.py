from flyway_test import views

__author__ = 'Sherlock'
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', views.find_users, name='index'),

    url(r'^get_users$', views.get_users, name='get_users'),

    url(r'^migrate$', views.migrate, name='migrate'),

)