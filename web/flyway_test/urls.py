from flyway_test import views

__author__ = 'Sherlock'
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', views.find_users, name='index'),

    url(r'^get_users$', views.get_users, name='get_users'),

    url(r'^get_images$', views.get_images, name='get_images'),

    url(r'^get_roles$', views.get_roles, name='get_roles'),

    url(r'^get_vms$', views.get_vms, name='get_vms'),

    url(r'^get_flavors$', views.get_flavors, name='get_flavors'),

    url(r'^get_keypairs$', views.get_keypairs, name='get_keypairs'),

    url(r'^get_tenants$', views.get_tenants, name='get_tenants'),

    url(r'^migrate$', views.migrate, name='migrate'),

)