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

from flyway.utils.utils import *

LOG = logging.getLogger(__name__)


class UserMigrationTask(task.Task):
    """
    Task to migrate all user info from the source cloud to the target cloud.
    """

    def __init__(self, name=None, provides=None, requires=None,
                 auto_extract=True, rebind=None):
        super(UserMigrationTask, self).__init__(name=None, provides=None,
                                                requires=None,
                                                auto_extract=True, rebind=None)
        self.message = 'Please update your OpenStack account password ' \
                       'as soon as possible!\nHere is a temporary password!'
        self.login = ''
        self.password = ''
        self.subject = 'Update OpenStack Password'
        self.from_addr = ''

    def execute(self):
        LOG.info('Migrating all users ...')

        ks_source_credentials = get_source_keystone_credentials()
        ks_target_credentials = get_target_keystone_credentials()

        ks_source = get_keystone_client(**ks_source_credentials)
        ks_target = get_keystone_client(**ks_target_credentials)

        target_userNames = {}
        for target_user in ks_target.users.list():
            target_userNames[target_user.name] = target_user.email

        for source_user in ks_source.users.list():
            if source_user.name not in target_userNames.keys():
                newPassword = generate_new_password()
                ks_target.users.create(name=source_user.name,
                                       password=newPassword,
                                       email=source_user.email)

                #Send emails
                send_email(from_addr=self.from_addr,
                          to_addr_list=[source_user.email],
                          cc_addr_list=[],
                          subject=self.subject,
                          message=self.message + 'Password:\n   ' + newPassword,
                          login=self.login,
                          password=self.password)

        for user in ks_source.users.list():
            LOG.debug(user)