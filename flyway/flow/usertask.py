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

from utils.helper import *
from utils.db_base import *
import time
import random
import smtplib

from taskflow import task

LOG = logging.getLogger(__name__)



class UserMigrationTask(task.Task):
    """
    Task to migrate all user info from the source cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(UserMigrationTask, self).__init__(**kwargs)
        clients = Clients()
        self.ks_source = clients.get_keystone_source()
        self.ks_target = clients.get_keystone_target()

        self.target_user_names = []
        for user in self.ks_target.users.list():
            self.target_user_names.append(user.name)
        print self.target_user_names

        self.initialise_db()


    def migrate_one_user(self, user):

        if user.name not in self.target_user_names:
            password = self.generate_new_password()

            self.ks_target.users.create(user.name,
                                        password,
                                        user.email,
                                        enabled=True)

            set_dict = {'completed':'YES'}
            where_dict = {'name': user.name}
            start = time.time()
            while True:
                if time.time() - start > 10:
                    print 'Fail!!!'
                    break
                elif self.migration_succeed(user):
                    update_table('users', set_dict, where_dict, False)
                    break

    #TODO Add Roles to user
        """roles = self.ks_source.roles.roles_for_user(source_user)
        self.ks_target.roles.add_user_role(target_user, roles)"""
        #TODO Assign user to the typical project


    def migration_succeed(self, user):
        for target_user in self.ks_target.users.list():
            if user.name == target_user.name:
                return True

        return False


    def execute(self):
        LOG.info('Migrating all keypairs ...')

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
                values.append("null, '{0}', '{1}', 'NO'".format(user.name, user.email))

        insert_record('users', values, False)


    def generate_new_password(self):
        """Generate a new password containing 10 letters
        """
        letters = 'abcdegfhijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        password = ''
        for i in range(10):
            ranNum = int(random.random() * len(letters))
            password += letters[ranNum]
        return password


    def send_email(self, from_addr, to_addr_list, cc_addr_list, subject, message,
                   login, password, smtpserver='smtp.gmail.com:587'):
        """Send email using gmail
        """
        header = 'From: %s\n' % from_addr
        header += 'To: %s\n' % ','.join(to_addr_list)
        header += 'Cc: %s\n' % ','.join(cc_addr_list)
        header += 'Subject: %s\n\n' % subject
        message = header + message

        server = smtplib.SMTP(smtpserver)
        server.starttls()
        server.login(login, password)
        problems = server.sendmail(from_addr, to_addr_list, message)
        server.quit()
