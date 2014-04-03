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

import logging
import sys
sys.path.append('../')

from taskflow import task
import keystoneclient.v2_0.client as ksclient

from flyway.common import config as cfg

LOG = logging.getLogger(__name__)


def find_all_users_in(keystone_client, tenant_id=None, limit=None, marker=None):
    LOG.info('Get all users in ')
    LOG.info(keystone_client)
    return keystone_client.users.list(tenant_id, limit, marker)


class UserMigrationTask(task.Task):
    """
    Task to migrate all user info from the source cloud to the target cloud.
    """

    def __init__(self, **kwargs):
        super(UserMigrationTask, self).__init__(kwargs)
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

    def execute(self):  # TODO: How to deal with the token expiration?
        LOG.info('Migrating all users ...')

        source_users = find_all_users_in(self.ks_source)

        moved_users = self.immigrate_users_to_target(source_users)

        LOG.info("User immigration is finished")

        return moved_users

    def immigrate_user(self, source_user):  # TODO: Generate random pwd and email to the user
        target_user = self.ks_target.users.create(source_user.name, '123', source_user.email, enabled=True)
        #TODO Add Roles to user
        """roles = self.ks_source.roles.roles_for_user(source_user)
        self.ks_target.roles.add_user_role(target_user, roles)"""
        #TODO Assign user to the typical project

        return target_user

    def immigrate_users_to_target(self, source_users):
        target_users = find_all_users_in(self.ks_target)
        moved_users = []
        # I have no idea how to rewrite the __eq__ in ksclient.users.User,
        # which could make this code simpler...
        for user in source_users:
            found = False
            for t_user in target_users:
                if user.name == t_user.name:
                    found = True
                    break
            if not found:
                moved_users.append(self.immigrate_user(user))
        return moved_users

