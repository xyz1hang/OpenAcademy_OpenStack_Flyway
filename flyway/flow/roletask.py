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
from utils.db_base import *
from taskflow import task

LOG = logging.getLogger(__name__)

TABLE_NAME = 'role_mapping'
TABLE_COLUMNS = '''id INT NOT NULL AUTO_INCREMENT,
                    roleName VARCHAR(64) NOT NULL,
                    src_cloud VARCHAR(64) NOT NULL,
                    dst_cloud VARCHAR(64) NOT NULL,
                    state VARCHAR(10) NOT NULL,
                    PRIMARY KEY(id),
                    UNIQUE (roleName, src_cloud, dst_cloud)
                '''


class RoleMigrationTask(task.Task):
    """
    Task to migrate all roles and user-tenant role mapping from the source
    cloud to the target cloud.
    """

    def __init__(self, **kwargs):
        super(RoleMigrationTask, self).__init__(kwargs)
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.s_cloud = cfg.CONF.SOURCE.os_auth_url
        self.t_cloud = cfg.CONF.TARGET.os_auth_url

    @staticmethod
    def list_roles(keystone_client):
        return keystone_client.roles.list()

    def init_db(self):
        delete_all_data(TABLE_NAME)
        create_table(TABLE_NAME, TABLE_COLUMNS, False)
        roles_to_move = self.check()

        for role in roles_to_move:
            record = "'null', '"+role.name+"','"+self.s_cloud+"', '"+self.t_cloud+"', 'unknown'"
            print record
            insert_record(TABLE_NAME, [record], False)

    def migrate_one_role(self, source_role):
        target_role = self.ks_target.roles.create(source_role.name)
        update_table(TABLE_NAME, {'state': 'completed'}, {'roleName': source_role.name, 'src_cloud': self.s_cloud,
                                                          'dst_cloud': self.t_cloud}, True)

    def execute(self):
        LOG.debug('Migrating roles...........')
        roles_to_move = self.check()
        roles_in_target = self.list_roles(self.ks_target)
        moved_roles = []

        for role in roles_to_move:
            found = False
            for t_role in roles_in_target:
                if role.name == t_role.name:
                    found = True
                    break
            if not found:
                self.migrate_one_role(role)
                moved_roles.append(role.name)
        LOG.info("Role immigration is finished")
        return moved_roles

    def check(self):
        roles_in_source = self.list_roles(self.ks_source)
        roles_in_target = self.list_roles(self.ks_target)
        roles_to_move = []
        for role in roles_in_source:
            found = False
            for t_role in roles_in_target:
                if role.name == t_role.name:
                    found = True
                    break
            if not found:
                roles_to_move.append(role)
        return roles_to_move




