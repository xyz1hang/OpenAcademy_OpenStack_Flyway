from django.shortcuts import render

# Create your views here.
import sys
sys.path.insert(0, '/Users/Sherlock/Documents/Code/OpenStack/VagrantRoot/OpenAcademy_OpenStack_Flyway/flyway')
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