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
from taskflow.patterns import linear_flow as lf
from taskflow.patterns import unordered_flow as uf

from flavortask import FlavorMigrationTask
from usertask import UserMigrationTask
from tenanttask import TenantMigrationTask
from roletask import RoleMigrationTask
from imagetask import ImageMigrationTask
from keypairtask import KeypairMigrationTask
from instancetask import InstanceMigrationTask
from keypairtask_nova_db import KeypairNovaDBMigrationTask
from update_keypair_user_task import UpdateKeypairUserTask


def get_flow():
    flow = lf.Flow('main_flow').add(
        uf.Flow('user_tenant_migration_flow').add(
            # Note that creating users and tenants can happen in parallel and
            # hence it is part of unordered flow
            #UserMigrationTask('user_migration_task'),
            TenantMigrationTask('tenant_migration_task')
            #FlavorMigrationTask('flavor_migration_task')
        ),
        # TODO: Add other tasks to the flow e.g migrate image, private key etc.
        #RoleMigrationTask('role_migration_task'),
        #ImageMigrationTask('image_migration_task'),
        #KeypairMigrationTask('keypairs_migration_task')
        #KeypairNovaDBMigrationTask('Keypairs_migration_task')
        #InstanceMigrationTask('instances_migration_task')

        # after resource migration:
        #UpdateProjectsQuotaTask('update_projects_quotas')
        #UpdateKeypairUserTask('update_keypairs_user_ids')
    )

    return flow


def execute():
    flow = get_flow()
    # store: a dict for input data of "all tasks" in the flow
    # append the parameter your task needed in this store dict
    # The input data is then injected via execute() function
    # e.g store={'meow': 'meow_in', 'woof': 'woof_in'}
    # ...
    # execute(self, woof)
    #TODO: need to figure out a better way to allow user to specify
    #TODO: specific resource to migrate
    data_required = {'tenants_to_move': ['tenant_test']}
    eng = engines.load(flow, store=data_required)
    result = eng.run()
    return result
