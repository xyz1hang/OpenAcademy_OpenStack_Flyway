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
TABLE_NAME = 'users'


def update_user_complete(user):
    update_table(TABLE_NAME, {'state': 'completed'}, {'name': user.name,
                                                      'src_cloud': cfg.CONF.SOURCE.os_cloud_name,
                                                      'dst_cloud': cfg.CONF.TARGET.os_cloud_name}, False)
    LOG.info("User {0} succeeded to migrate, recorded in database".format(user))


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
            password = generate_new_password()

            try:
                migrated_user = self.ks_target.users.create(user.name,
                                                            password,
                                                            user.email,
                                                            enabled=True)
            except Exception, e:
                LOG.error("There is an error while migrating user {0}".format(user))
                LOG.error("The error is {0}".format(e))
            else:
                LOG.info("Succeed to migrate user {0}".format(user))
                update_user_complete(user)
        return migrated_user

    def initialise_users_mapping(self):

        if not check_table_exist(TABLE_NAME):
            table_columns = '''id INT NOT NULL AUTO_INCREMENT,
                           name VARCHAR(64) NOT NULL,
                           email VARCHAR(64),
                           src_cloud VARCHAR(64) NOT NULL,
                           dst_cloud VARCHAR(64) NOT NULL,
                           state VARCHAR(10) NOT NULL,
                           PRIMARY KEY(id),
                           UNIQUE (name, src_cloud, dst_cloud)
                        '''
            create_table(TABLE_NAME, table_columns, False)

        s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        t_cloud_name = cfg.CONF.TARGET.os_cloud_name
        init_string = "null, '{0}', '{1}', '"+s_cloud_name+"', '"+t_cloud_name+"', 'unknown'"
        LOG.debug("init_string: "+init_string)

        init_users = []
        for user in self.ks_source.users.list():
            if user.name not in self.target_user_names and not self.is_migrated(user):
                init_users.append(
                    init_string.format(user.name, user.email))
                LOG.debug("insert user:")
                LOG.debug(init_string.format(user.name, user.email))

        insert_record(TABLE_NAME, init_users, True)

    @staticmethod
    def is_migrated(user):
        filters = {
            "name": user.name,
            "src_cloud": cfg.CONF.SOURCE.os_cloud_name,
            "dst_cloud": cfg.CONF.TARGET.os_cloud_name,
            "state": "completed"
        }
        data = read_record(TABLE_NAME, ["0"], filters, True)
        return len(data) > 0

    def execute(self):
        LOG.info('Migrating all users ...')

        self.initialise_users_mapping()

        migrated_users = []
        for user in self.ks_source.users.list():
            migrated_user = self.migrate_one_user(user)
            if migrated_user is not None:
                migrated_users.append(migrated_user)

        # TODO delete the corresponding data when the task is finished
        delete_record(TABLE_NAME, {"src_cloud": cfg.CONF.SOURCE.os_cloud_name,
                                   "dst_cloud": cfg.CONF.TARGET.os_cloud_name,
                                   "state": "completed"})

        return migrated_users
