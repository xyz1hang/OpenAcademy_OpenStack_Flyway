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

from taskflow import task
#from common import config as cfg
from utils import *

LOG = logging.getLogger(__name__)


class TenantMigrationTask(task.Task):
    """
    Task to migrate all tenant (project) info from the source cloud to the
    target cloud.
    """

    def execute(self):
        LOG.info('Migrating all tenants ...')

	ks_source_credentials = getSourceKeystoneCredentials()
	ks_target_credentials = getTargetKeystoneCredentials()
	
	ks_source = getKeystoneClient(**ks_source_credentials)
	ks_target = getKeystoneClient(**ks_target_credentials)

	target_tenantNames = []
	for tenant in ks_target.tenants.list():
		target_tenantNames.append(tenant.name)

	for source_tenant in ks_source.tenants.list():
		if source_tenant.name not in target_tenantNames:
			ks_target.tenants.create(tenant_name=source_tenant.name)






        
	
