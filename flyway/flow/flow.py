# -*- coding: utf-8 -*-

#    Copyright (C) 2012 eBay, Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from taskflow import engines
from taskflow import task
from taskflow.patterns import linear_flow as lf
from taskflow.patterns import unordered_flow as uf

from flavortask import FlavorMigrationTask
from usertask import UserMigrationTask
from tenanttask import TenantMigrationTask
from roletask import RoleMigrationTask
from imagetask import ImageMigrationTask
from instancetask import InstanceMigrationTask
from keypairtask import KeypairMigrationTask
from update_keypair_user_task import UpdateKeypairUserTask
from update_projects_quotas_task import UpdateProjectsQuotasTask
from update_project_user_role_task import ProjectUserRoleBindingTask


class InputGatheringTask(task.Task):
    def __init__(self, input_data, **kwargs):
        super(InputGatheringTask, self).__init__(**kwargs)
        self.input_data = input_data if input_data else None

    def execute(self):
        if not self.input_data:
            self.input_data = {'users_to_move': None,
                               'tenants_to_move': None,
                               'flavors_to_migrate': None,
                               'images_to_migrate': None,
                               'tenant_to_process': None,
                               'keypairs_to_move': None,
                               'roles_to_migrate': None}
        return self.input_data


def get_flow(input_data=None):
    input_task = InputGatheringTask(input_data=input_data)
    user_task = UserMigrationTask('user_migration_task')
    tenant_task = TenantMigrationTask('tenant_migration_task')
    flavor_task = FlavorMigrationTask('flavor_migration_task')
    role_task = RoleMigrationTask('role_migration_task')
    image_task = ImageMigrationTask('image_migration_task')
    instance_task = InstanceMigrationTask('instances_migration_task')
    keypair_task = KeypairMigrationTask('Keypairs_migration_task')

    proj_quota_task = UpdateProjectsQuotasTask('update_projects_quotas')
    keypair_update_task = UpdateKeypairUserTask('update_keypairs_user_ids')
    pr_binding_task = ProjectUserRoleBindingTask('project_roles_bind_task')

    flow = lf.Flow('main_flow').add(
        task.FunctorTask(input_task.execute, provides={'users_to_move',
                                                       'tenants_to_move',
                                                       'flavors_to_migrate',
                                                       'images_to_migrate',
                                                       'tenant_to_process',
                                                       'keypairs_to_move',
                                                       'roles_to_migrate'}),
        uf.Flow('user_tenant_migration_flow').add(
            # Note that creating users, tenants, flavor and role can happen in
            # parallel and hence it is part of unordered flow
            task.FunctorTask(user_task.execute, name='user_task',
                             rebind={'users_to_move': "users_to_move"}),
            task.FunctorTask(tenant_task.execute, name='tenant_task',
                             rebind={'tenants_to_move': "tenants_to_move"}),
            task.FunctorTask(flavor_task.execute, name='flavor_task',
                             rebind={
                                 'flavors_to_migrate': "flavors_to_migrate"}),
            task.FunctorTask(role_task.execute, name='role_task',
                             rebind={'roles_to_migrate': "roles_to_migrate"}),
            # UserMigrationTask('user_migration_task'),
            # TenantMigrationTask('tenant_migration_task'),
            # FlavorMigrationTask('flavor_migration_task'),
            # RoleMigrationTask('role_migration_task')
        ),
        # TODO: Add other tasks to the flow e.g migrate image, private key etc.
        task.FunctorTask(image_task.execute, name='image_task',
                         rebind={'images_to_migrate': "images_to_migrate",
                                 'tenant_to_process': 'tenant_to_process'}),
        task.FunctorTask(keypair_task.execute, name='keypair_task',
                         rebind={'keypairs_to_move': "keypairs_to_move"}),
        # task.FunctorTask(instance_task.execute, name='instance_task',
        #                  rebind={'tenant_vm_dicts': "tenant_vm_dicts"}),

        # post migration task:
        task.FunctorTask(proj_quota_task.execute,
                         name='update_project_quota_task'),
        task.FunctorTask(keypair_update_task.execute,
                         name='update_user_keypair_task'),
        task.FunctorTask(pr_binding_task.execute,
                         name='project_role_binding_task')

        # ImageMigrationTask('image_migration_task'),
        # KeypairMigrationTask('Keypairs_migration_task'),
        # # InstanceMigrationTask('instances_migration_task')
        #
        # # after resource migration:
        # UpdateProjectsQuotasTask('update_projects_quotas'),
        # UpdateKeypairUserTask('update_keypairs_user_ids'),
        # ProjectUserRoleBindingTask('bind project_user_roles')
    )

    return flow


def execute(input_data=None):
    flow = get_flow(input_data)
    # store: a dict for input data of "all tasks" in the flow
    # append the parameter your task needed in this store dict
    # The input data is then injected via execute() function
    # e.g store={'meow': 'meow_in', 'woof': 'woof_in'}
    # ...
    # execute(self, woof)
    #TODO: need to figure out a better way to allow user to specify
    #TODO: specific resource to migrate

    # resources specified to migrate are given through an argument "values",
    # “values” is a dictionary that all keys correspond to types of resources,
    # and values are the specified resources (None means migrating all
    # resources on the source cloud, [] means migrating nothing)

    # tenants = values.get('tenants_to_move', None) if values else None
    # flavors = values.get('flavors_to_migrate', None) if values else None
    # images = values.get('images_to_migrate', None) if values else None
    # keypairs = values.get('keypairs_to_move', None) if values else None
    # image_tenants = values.get('tenant_to_process', None) if values else None
    # roles = values.get('name_of_roles_to_move', None) if values else None
    #
    # data_required = {'tenants_to_move': tenants,
    #                  'flavors_to_migrate': flavors,
    #                  'images_to_migrate': images,
    #                  'tenant_to_process': keypairs,
    #                  'keypairs_to_move': image_tenants,
    #                  'name_of_roles_to_move': roles}

    eng = engines.load(flow)
    result = eng.run()
    return result