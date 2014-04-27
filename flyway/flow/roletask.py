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

from utils.helper import *
from utils.db_handlers.roles import *
from taskflow import task

LOG = logging.getLogger(__name__)


class RoleMigrationTask(task.Task):
    """
    Task to migrate all roles and user-tenant role mapping from the source
    cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(RoleMigrationTask, self).__init__(*args, **kwargs)
        # get keystone client for source and target clouds
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

    @staticmethod
    def list_roles(keystone_client):
        return keystone_client.roles.list()

    @staticmethod
    def list_names(roles):
        return [role.name for role in roles]

    def get_roles_to_move(self):
        roles_in_source = self.list_roles(self.ks_source)
        target_role_names = self.list_names(self.ks_target.roles.list())
        return [role for role in roles_in_source
                if role.name not in target_role_names]

    def migrate_one_role(self, role_to_move):
        try:
            role_moved = self.ks_target.roles.create(role_to_move.name)
            set_complete(role_moved.name)
        except:
            set_error(role_to_move.name)
            LOG.info("migrating "+role_to_move.name+" failed")

    def execute(self, roles_to_migrate):
        if type(roles_to_migrate) is list and \
           len(roles_to_migrate) == 0:
            return

        LOG.debug('Migrating roles...........')
        roles_to_move = self.get_roles_to_move()
        initialise_roles_mapping(self.list_names(roles_to_move))
        if roles_to_migrate is None:
            for role in roles_to_move:
                self.migrate_one_role(role)
        else:
            for role in roles_to_move:
                if role.name in roles_to_migrate:
                    self.migrate_one_role(role)

        LOG.info("Role Migration is finished")
