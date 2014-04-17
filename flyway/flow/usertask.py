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
from utils.db_handlers.users import set_user_complete, delete_migrated_users, initialise_users_mapping

from utils.helper import *

from taskflow import task

LOG = logging.getLogger(__name__)


class UserMigrationTask(task.Task):
    """
    Task to migrate all user info from the source cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(UserMigrationTask, self).__init__(*args, **kwargs)
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.target_user_names = [user.name for user in self.ks_target.users.list()]

    def migrate_one_user(self, user):
        LOG.info("Begin to migrate user {0}".format(user))
        migrated_user = None
        if user.name not in self.target_user_names:
            password = self.generate_new_password(user)

            try:
                migrated_user = self.ks_target.users.create(user.name,
                                                            password,
                                                            user.email,
                                                            enabled=True)
            except Exception, e:
                LOG.error("There is an error while migrating user {0}"
                          .format(user))
                LOG.error("The error is {0}".format(e))
            else:
                LOG.info("Succeed to migrate user {0}".format(user))
                set_user_complete(user)
        return migrated_user

    @staticmethod
    def generate_new_password(user, default_password='123456'):
        """
        Generate a random password for the user and email to the user,
        default_password is used if the user has no email
        """
        if user.email is not None:
            password = generate_new_password()
            send_reset_password_email(user.email, password)
        else:
            password = default_password

        return password

    def execute(self):
        LOG.info('Migrating all users ...')

        initialise_users_mapping(self.ks_source, self.target_user_names)

        migrated_users = []
        for user in self.ks_source.users.list():
            migrated_user = self.migrate_one_user(user)
            if migrated_user is not None:
                migrated_users.append(migrated_user)

        delete_migrated_users()

        return migrated_users
