import json
from django.http import HttpResponse

# Create your views here.
import sys
sys.path.insert(0, '../flyway')

from utils.db_handlers.environment_config import initialize_environment, update_environment
from flow.flavortask import FlavorMigrationTask
from flow.imagetask import ImageMigrationTask
from flow.keypairtask import KeypairMigrationTask
from flow.roletask import RoleMigrationTask
from flow.tenanttask import TenantMigrationTask
from flow.instancetask import InstanceMigrationTask
from utils.db_handlers.keypairs import *
from utils.db_base import *
from utils.helper import *

from flow import flow

from django.shortcuts import render
from flow.usertask import UserMigrationTask
from common import config as cfg

cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
cfg.setup_logging()
initialize_environment()
update_environment()


def index(request):
    latest_poll_list = [1, 2, 3, 4, 5]
    context = {'latest_poll_list': latest_poll_list}
    return render(request, 'flyway_test/index.html', context)


def find_users(request):
    migration_task = UserMigrationTask()
    users = migration_task.ks_source.users.list()
    context = {'users': users}
    return render(request, 'flyway_test/index.html', context)


def get_users(request):
    migration_task = UserMigrationTask()
    users = migration_task.ks_source.users.list()
    return_users = [{'name': user.name,
                     'id': user.id} for user in users]
    return HttpResponse(json.dumps(return_users, ensure_ascii=False))


def get_roles(request):
    migration_task = RoleMigrationTask()
    roles = migration_task.ks_source.roles.list()
    return_roles = [{'name': role.name,
                     'id': role.id} for role in roles]
    return HttpResponse(json.dumps(return_roles, ensure_ascii=False))


def get_flavors(request):
    migration_task = FlavorMigrationTask('')
    flavors = migration_task.nv_source.flavors.list()
    return_flavors = [{'name': flavor.name,
                       'id': flavor.id} for flavor in flavors]
    return HttpResponse(json.dumps(return_flavors, ensure_ascii=False))


def get_keypairs(request):
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
    migration_task = TenantMigrationTask('')
    tenants = migration_task.ks_source.tenants.list()
    return_tenants = [{'name': tenant.name,
                       'id': tenant.id} for tenant in tenants]
    return HttpResponse(json.dumps(return_tenants, ensure_ascii=False))


def get_vms(request):
    s_host = cfg.CONF.SOURCE.os_auth_url.split("http://")[1].split(":")[0]
    data = get_info_from_openstack_db(table_name="instances",
                                      db_name='nova',
                                      host=s_host,
                                      columns=['project_id', 'uuid',
                                               'hostname'],
                                      filters={})
    tenant_vms = []
    for one_data in data:
        tenant_name = get_info_from_openstack_db(table_name="project",
                                                 db_name='keystone',
                                                 host=s_host,
                                                 columns=['name'],
                                                 filters={'id': one_data[0]})
        tenant_vms.append({"name": tenant_name[0], "id": one_data[1],
                           "host_name": one_data[2]})

    return_vms = [{'name': tenant_vm["name"],
                   'id': tenant_vm["id"],
                   'host_name':
                   tenant_vm["host_name"]} for tenant_vm in tenant_vms]
    return HttpResponse(json.dumps(return_vms, ensure_ascii=False))


def get_images(request):
    migration_task = ImageMigrationTask('')
    images = migration_task.gl_source.images.list()
    return_images = [{'name': image.name,
                      'id': image.id} for image in images]
    return HttpResponse(json.dumps(return_images, ensure_ascii=False))


def migrate(request):
    json_data = request.GET.get('data_to_migrate')
    data = json.loads(json_data)

    tenants = data.get('tenant')
    flavors = data.get('flavor')
    images = data.get('image')
    keypairs = data.get('keypair')
    roles = data.get('role')
    users = data.get('user')
    vms = data.get('vm')

    refined_data = {'tenants_to_move': tenants,
                    'flavors_to_migrate': flavors,
                    'images_to_migrate': images,
                    'keypairs_to_move': keypairs,
                    'roles_to_migrate': roles,
                    'users_to_move': users,
                    'tenant_vm_dicts': vms,
                    'tenant_to_process': []}

    result = flow.execute(refined_data)
    return HttpResponse(json.dumps(result, ensure_ascii=False))


def migrate_all(request):
    result = flow.execute(None)
    return HttpResponse(json.dumps(result, ensure_ascii=False))
