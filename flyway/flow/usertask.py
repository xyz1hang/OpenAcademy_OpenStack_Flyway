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
import time

from taskflow import task

LOG = logging.getLogger(__name__)


class UserMigrationTask(task.Task):
    """
    Task to migrate all user info from the source cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(UserMigrationTask, self).__init__(**kwargs)
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.target_user_names = []
        for user in self.ks_target.users.list():
            self.target_user_names.append(user.name)
        print self.target_user_names

        self.initialise_db()

    def migrate_one_user(self, user):

        if user.name not in self.target_user_names:
            password = generate_new_password()

            self.ks_target.users.create(user.name,
                                        password,
                                        user.email,
                                        enabled=True)

            set_dict = {'completed': 'YES'}
            where_dict = {'name': user.name}
            start = time.time()
            while True:
                if time.time() - start > 10:
                    print 'Fail!!!'
                    break
                elif self.migration_succeed(user):
                    update_table('users', set_dict, where_dict, False)
                    break

    def migration_succeed(self, user):
        for target_user in self.ks_target.users.list():
            if user.name == target_user.name:
                return True

        return False

    def execute(self):
        LOG.info('Migrating all users ...')

        for user in self.ks_source.users.list():
            self.migrate_one_user(user)

    def initialise_db(self):

        table_columns = '''id INT NOT NULL AUTO_INCREMENT,
                           name VARCHAR(64) NOT NULL,
                           email VARCHAR(64) NOT NULL,
                           completed VARCHAR(10) NOT NULL,
                           PRIMARY KEY(id),
                           UNIQUE (name)
                        '''

        if not check_table_exist('users'):
            create_table('users', table_columns, False)

        values = []
        for user in self.ks_source.users.list():
            if user.name not in self.target_user_names:
                values.append(
                    "null, '{0}', '{1}', 'NO'".format(user.name, user.email))

        insert_record('users', values, False)
