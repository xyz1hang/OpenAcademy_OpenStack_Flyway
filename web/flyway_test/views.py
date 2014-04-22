import json
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
import sys
sys.path.insert(0, '../flyway')
from flow.flavortask import FlavorMigrationTask
from flow.imagetask import ImageMigrationTask
from flow.keypairtask_nova_db import KeypairNovaDBMigrationTask
from flow.roletask import RoleMigrationTask
from flow.tenanttask import TenantMigrationTask

import os
from flow import flow


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


def get_roles(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = RoleMigrationTask()
    roles = migration_task.ks_source.roles.list()
    return_roles = [{
        'name': role.name,
        'id': role.id
    } for role in roles]
    return HttpResponse(json.dumps(return_roles, ensure_ascii=False))


def get_flavors(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = FlavorMigrationTask('')
    flavors = migration_task.nv_source.flavors.list()
    return_flavors = [{
        'name': flavor.name,
        'id': flavor.id
    } for flavor in flavors]
    return HttpResponse(json.dumps(return_flavors, ensure_ascii=False))


def get_keypairs(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = KeypairNovaDBMigrationTask('')
    keypairs = migration_task.nv_source.keypairs.list()
    return_keypairs = [{
        'name': keypair.name,
        'fingerprint': keypair.fingerprint
    } for keypair in keypairs]
    return HttpResponse(json.dumps(return_keypairs, ensure_ascii=False))


def get_tenants(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = TenantMigrationTask('')
    tenants = migration_task.ks_source.tenants.list()
    return_tenants = [{
        'name': tenant.name,
        'id': tenant.id
    } for tenant in tenants]
    return HttpResponse(json.dumps(return_tenants, ensure_ascii=False))


def get_vms(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    # TODO: what task ??
    migration_task = UserMigrationTask()
    vms = migration_task.nv_source.vms.list()
    return_vms = [{
        'name': vm.name,
        'id': vm.id
    } for vm in vms]
    return HttpResponse(json.dumps(return_vms, ensure_ascii=False))


def get_images(request):
    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])
    migration_task = ImageMigrationTask('')
    images = migration_task.gl_source.images.list()
    return_images = [{
        'name': image.name,
        'id': image.id
    } for image in images]
    return HttpResponse(json.dumps(return_images, ensure_ascii=False))


def migrate(request):
    json_data = request.GET.get('data_to_migrate')
    data = json.loads(json_data)

    cfg.parse(['--config-file', '../flyway/etc/flyway.conf'])

    refined_data = {
        'users_to_move': data['user'],
        'name_of_roles_to_move': data['role'],
        'images_to_migrate': data['image'],
        'tenants_to_move': data['tenant'],
        'keypairs_to_move': data['keypair'],
        'flavors_to_migrate': data['flavor'],
        'tenant_to_process': data['tenant']
    }
    print "data:"
    print refined_data
    result = flow.execute(refined_data)
    return HttpResponse(json.dumps(result, ensure_ascii=False))


