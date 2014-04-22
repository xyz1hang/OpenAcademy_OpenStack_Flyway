import json
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
import sys
import os
from flow import flow

sys.path.insert(0, '../flyway')
from django.shortcuts import render
from flow.usertask import UserMigrationTask
from common import config as cfg


def index(request):
    latest_poll_list = [1,2,3,4,5]
    context = {'latest_poll_list': latest_poll_list}
    return render(request, 'flyway_test/index.html', context)


def find_users(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = UserMigrationTask()
    users = migration_task.ks_source.users.list()
    context = {'users': users}
    return render(request, 'flyway_test/index.html', context)


def get_users(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = UserMigrationTask()
    users = migration_task.ks_source.users.list()
    return_users = [{
        'name': user.name,
        'id': user.id
    } for user in users]
    return HttpResponse(json.dumps(return_users, ensure_ascii=False))


def migrate(request):
    print request.GET
    json_data = request.GET.get('data_to_migrate')[0]
    data = json.loads(json_data)
    print data
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    flow.execute(data)

