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
    cfg.StrOpt('os_auth_url', default='0.0.0.0'),
    cfg.StrOpt('os_tenant_id'),
    cfg.StrOpt('os_tenant_name', default='admin'),
    cfg.StrOpt('os_username', default='admin'),
    cfg.StrOpt('os_password')
]

log_opts = [
    cfg.StrOpt('loglevel', default='INFO'),
    cfg.StrOpt('logfile', default='./flyway.log'),
    cfg.StrOpt('logformat', default=None)
]

CONF = cfg.CONF

source_group = cfg.OptGroup(name='SOURCE', title='Source Openstack Options')
CONF.register_group(source_group)
CONF.register_opts(opts, source_group)

target_group = cfg.OptGroup(name='TARGET', title='Target Openstack Options')
CONF.register_group(target_group)
CONF.register_opts(opts, target_group)

CONF.register_opts(log_opts)


def parse(args):
    cfg.CONF(args=args, project='flyway', version='0.1')


def setup_logging():
    logging.basicConfig(level=CONF.loglevel)
    handler = logging.handlers.WatchedFileHandler(CONF.logfile, mode='a')
    formatter = logging.Formatter(CONF.logformat)
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    LOG.info("Logging enabled!")