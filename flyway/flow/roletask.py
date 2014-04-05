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

import logging
import sys
sys.path.append('../')

from taskflow import task
import keystoneclient.v2_0.client as ksclient

from flyway.common import config as cfg

LOG = logging.getLogger(__name__)


def find_all_roles_in(keystone_client):
    LOG.info('Get all roles in ')
    LOG.info(keystone_client)
    return keystone_client.roles.list()


class RoleMigrationTask(task.Task):
    """
    Task to migrate all roles and user-tenant role mapping from the source
    cloud to the target cloud.
    """

    def __init__(self, **kwargs):
        super(RoleMigrationTask, self).__init__(kwargs)
        ks_source = ksclient.Client(username=cfg.CONF.SOURCE.os_username,
                                    password=cfg.CONF.SOURCE.os_password,
                                    auth_url=cfg.CONF.SOURCE.os_auth_url,
                                    tenant_name=cfg.CONF.SOURCE.os_tenant_name)
        ks_target = ksclient.Client(username=cfg.CONF.TARGET.os_username,
                                    password=cfg.CONF.TARGET.os_password,
                                    auth_url=cfg.CONF.TARGET.os_auth_url,
                                    tenant_name=cfg.CONF.TARGET.os_tenant_name)
        self.ks_source = ksclient.Client(endpoint=cfg.CONF.SOURCE.os_keystone_endpoint,
                                         token=ks_source.auth_token)
        self.ks_target = ksclient.Client(endpoint=cfg.CONF.TARGET.os_keystone_endpoint,
                                         token=ks_target.auth_token)

    def execute(self):
        LOG.debug('Inside role migration task...........')

        source_roles = find_all_roles_in(self.ks_source)

        moved_roles = self.immigrate_roles_to_target(source_roles)

        LOG.info("Role immigration is finished")

        return moved_roles

    def immigrate_role(self, source_role):
        target_role = self.ks_target.roles.create(source_role.name)
        return target_role

    def immigrate_roles_to_target(self, source_roles):
        target_roles = find_all_roles_in(self.ks_target)
        moved_roles = []
        print source_roles
        for role in source_roles:
            found = False
            for t_role in target_roles:
                if role.name == t_role.name:
                    found = True
                    break
            if not found:
                moved_roles.append(self.immigrate_role(role))
        return moved_roles