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

import sys
sys.path.append('../')

from taskflow import task
from flyway.utils.db_handler import update_tenant_table
from flyway.utils import db_handler
from flyway.utils import exceptions
from flyway.utils.helper import *
from flyway.utils.resourcetype import ResourceType
from keystoneclient import exceptions as keystone_exceptions

LOG = logging.getLogger(__name__)


class TenantMigrationTask(task.Task):
    """
    Task to migrate all tenant (project) info from the source cloud to the
    target cloud.
    """

    def __init__(self, name, *args, **kwargs):
        super(TenantMigrationTask, self).__init__(name, **kwargs)
        self.ks_source = None
        self.ks_target = None
        self.tenants_to_move = args

    def migrate_one_tenant(self, tenant_name):
        try:
            s_tenant = self.ks_source.tenants.find(name=tenant_name)
        except keystone_exceptions.NotFound:
            raise exceptions.ResourceNotFoundException(
                ResourceType.tenant, tenant_name,
                cfg.CONF.SOURCE.os_cloud_name)

        s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        # check whether the tenant has been migrated
        values = [tenant_name, s_cloud_name]
        m_tenant = db_handler.get_migrated_tenant(values)

        if m_tenant is not None:
            print("tenant {0} in cloud {1} has already been migrated"
                  .format(m_tenant["project_name"], s_cloud_name))

        elif m_tenant is None:
            # check for tenant name duplication
            new_tenant_name = s_tenant.name
            migrated_tenant = s_tenant
            try:
                found = self.ks_target.tenants.find(name=s_tenant.name)
                print 'found: ' + str(found)
                if found:
                    user_input = \
                        raw_input("duplicated tenant {0} found on "+
                                  "cloud {1}\nPlease type in a new name or "+
                                  "'abort':".format(found.name, t_cloud_name))
                    if user_input is "abort":
                        # TODO: implement cleaning up and proper exit
                        return None
                    elif user_input:
                        new_tenant_name = user_input
                        migrated_tenant = self.ks_target.tenants.create(
                            new_tenant_name, s_tenant.description, True)
            except keystone_exceptions.NotFound:
                # create a new tenant
                migrated_tenant = self.ks_target.tenants.create(
                    new_tenant_name, s_tenant.description, True)

            # add the "admin" as the default user - admin - of
            # the tenant migrated.
            # Actual users involved in the tenant can be
            # added in and replace default one later
            admin = self.ks_target.users.find(name="admin")
            role = self.ks_target.roles.find(name="admin")
            migrated_tenant.add_user(admin, role)

            # record in database
            # TODO: need to catch other exception in case of
            # TODO: creating failure and update the state accordingly
            tenant_data = {'project_name': s_tenant.name,
                           'src_uuid': s_tenant.id,
                           'src_cloud': s_cloud_name,
                           'new_project_name': new_tenant_name,
                           'dst_uuid': migrated_tenant.id,
                           'dst_cloud': t_cloud_name,
                           'state': "completed"}

            db_handler.record_tenant_migrated(**tenant_data)

    def execute(self):

        """execute the tenant migration task

        :param tenants_to_move: the tenant to move. If the not specified
        or length equals to 0 all tenant will be migrated, otherwise only
        specified tenant will be migrated
        """
        # initialise python clients(e.g keystone) after
        # execution begin i.e after config is ready
        clients = get_clients()
        self.ks_source = clients.get_source()
        self.ks_target = clients.get_destination()

        update_tenant_table()

        if not self.tenants_to_move or len(self.tenants_to_move) == 0:
            LOG.info('Migrating all tenants ...')
            tenants_to_move = []
            for tenant in self.ks_source.tenants.list():
                tenants_to_move.append(tenant.name)
        else:
            LOG.info('Migrating given tenants of size {0} ...\n'
                     .format(len(self.tenants_to_move)))

        for source_tenant in self.tenants_to_move:
            LOG.info('Migrating tenant {0}\n'.format(source_tenant))
            self.migrate_one_tenant(source_tenant)