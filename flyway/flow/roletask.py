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

from utils.helper import *
from taskflow import task

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
        self.ks_source = None
        self.ks_target = None

    def execute(self):
        LOG.debug('Migrating roles...........')

        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        source_roles = find_all_roles_in(self.ks_source)

        moved_roles = self.migrate_roles_to_target(source_roles)

        LOG.info("Role immigration is finished")

        return moved_roles

    def migrate_role(self, source_role):
        target_role = self.ks_target.roles.create(source_role.name)
        return target_role

    def migrate_roles_to_target(self, source_roles):
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
                moved_roles.append(self.migrate_role(role))
        return moved_roles
