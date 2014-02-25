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

import taskflow.engines
from taskflow.patterns import linear_flow as lf
from taskflow.patterns import unordered_flow as uf

from usertask import UserMigrationTask
from tenanttask import TenantMigrationTask
from roletask import RoleMigrationTask


flow = lf.Flow('main_flow').add(
    uf.Flow('user_tenant_migration_flow').add(
        # Note that creating users and tenants can happen in parallel and
        # hence it is part of unordered flow
        UserMigrationTask('user_migration_task'),
        TenantMigrationTask('tenant_migration_task')
    ),
    RoleMigrationTask('role_migration_task')
    # TODO: Add other tasks to the flow
)


def execute():
    result = taskflow.engines.run(flow, engine_conf='parallel')
    return result