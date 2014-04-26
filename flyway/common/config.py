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
import logging.config
import logging.handlers

from oslo.config import cfg


LOG = logging.getLogger(__name__)

opts = [
    cfg.StrOpt('os_auth_url', default=None),
    cfg.StrOpt('os_tenant_name', default='admin'),
    cfg.StrOpt('os_username', default='admin'),
    cfg.StrOpt('os_password'),
    cfg.StrOpt('os_cloud_name')
]

log_opts = [
    cfg.StrOpt('log_level', default='INFO'),
    cfg.StrOpt('log_file', default='./flyway.log'),
    cfg.StrOpt('log_format', default=None)
]

db_opts = [
    cfg.StrOpt('host', default='localhost'),
    cfg.StrOpt('user', default='root'),
    cfg.StrOpt('mysql_password', default=None),
    cfg.StrOpt('db_name', default='flyway')
]

email_opts = [
    cfg.StrOpt('smtpserver', default='smtp.gmail.com:587'),
    cfg.StrOpt('login'),
    cfg.StrOpt('password')
]

CONF = cfg.CONF

source_group = cfg.OptGroup(name='SOURCE', title='Source OpenStack Options')
CONF.register_group(source_group)
CONF.register_opts(opts, source_group)

target_group = cfg.OptGroup(name='TARGET', title='Target OpenStack Options')
CONF.register_group(target_group)
CONF.register_opts(opts, target_group)

CONF.register_opts(log_opts)

db_group = cfg.OptGroup(name='DATABASE', title='Database Credentials')
CONF.register_group(db_group)
CONF.register_opts(db_opts, db_group)

email_group = cfg.OptGroup(name='EMAIL', title='Email Credentials')
CONF.register_group(email_group)
CONF.register_opts(email_opts, email_group)


def parse(args):
    cfg.CONF(args=args, project='flyway', version='0.1')
    

def setup_logging():
    logging.basicConfig(level=CONF.log_level)
    handler = logging.handlers.WatchedFileHandler(CONF.log_file, mode='a')
    formatter = logging.Formatter(CONF.log_format)
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    LOG.info("Logging enabled!")
