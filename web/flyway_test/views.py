import json
from django.http import HttpResponse

# Create your views here.
import sys

sys.path.insert(0, '../flyway')
from flow.flavortask import FlavorMigrationTask
from flow.imagetask import ImageMigrationTask
from flow.keypairtask import KeypairMigrationTask
from flow.roletask import RoleMigrationTask
from flow.tenanttask import TenantMigrationTask
from utils.db_handlers.keypairs import *

from flow import flow

from django.shortcuts import render
from flow.usertask import UserMigrationTask
from common import config as cfg


def index(request):
    latest_poll_list = [1, 2, 3, 4, 5]
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
    return_users = [{'name': user.name,
                     'id': user.id} for user in users]
    return HttpResponse(json.dumps(return_users, ensure_ascii=False))


def get_roles(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = RoleMigrationTask()
    roles = migration_task.ks_source.roles.list()
    return_roles = [{'name': role.name,
                     'id': role.id} for role in roles]
    return HttpResponse(json.dumps(return_roles, ensure_ascii=False))


def get_flavors(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = FlavorMigrationTask('')
    flavors = migration_task.nv_source.flavors.list()
    return_flavors = [{'name': flavor.name,
                       'id': flavor.id} for flavor in flavors]
    return HttpResponse(json.dumps(return_flavors, ensure_ascii=False))


def get_keypairs(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = KeypairMigrationTask('')
    data = get_info_from_openstack_db(table_name="key_pairs",
                                      db_name='nova',
                                      host=migration_task.s_host,
                                      columns=['name', 'fingerprint'],
                                      filters={"deleted": '0'})
    return_keypairs = [{'name': pair[0],
                        'fingerprint': pair[1]} for pair in data]
    return HttpResponse(json.dumps(return_keypairs, ensure_ascii=False))


def get_tenants(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = TenantMigrationTask('')
    tenants = migration_task.ks_source.tenants.list()
    return_tenants = [{'name': tenant.name,
                       'id': tenant.id} for tenant in tenants]
    return HttpResponse(json.dumps(return_tenants, ensure_ascii=False))


def get_vms(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    # TODO: what task ??
    migration_task = UserMigrationTask()
    vms = migration_task.nv_source.vms.list()
    return_vms = [{'name': vm.name,
                   'id': vm.id} for vm in vms]
    return HttpResponse(json.dumps(return_vms, ensure_ascii=False))


def get_images(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = ImageMigrationTask('')
    images = migration_task.gl_source.images.list()
    return_images = [{'name': image.name,
                      'id': image.id} for image in images]
    return HttpResponse(json.dumps(return_images, ensure_ascii=False))


def migrate(request):
    json_data = request.GET.get('data_to_migrate')
    data = json.loads(json_data)

    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])

    tenants = data.get('tenants_to_move', None) if data else None
    flavors = data.get('flavors_to_migrate', None) if data else None
    images = data.get('images_to_migrate', None) if data else None
    keypairs = data.get('keypairs_to_move', None) if data else None
    image_tenants = data.get('tenant_to_process', None) if data else None
    roles = data.get('roles_to_migrate', None) if data else None
    users = data.get('users_to_move', None) if data else None

    refined_data = {'tenants_to_move': tenants,
                    'flavors_to_migrate': flavors,
                    'images_to_migrate': images,
                    'tenant_to_process': keypairs,
                    'keypairs_to_move': image_tenants,
                    'roles_to_migrate': roles,
                    'users_to_move': users}
    print "data:"
    print refined_data
    result = flow.execute(refined_data)
    return HttpResponse(json.dumps(result, ensure_ascii=False))


