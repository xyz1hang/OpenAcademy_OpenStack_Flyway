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

from taskflow import task
from common import config as cfg
from utils import *

LOG = logging.getLogger(__name__)

class InstanceMigrationTask(task.Task):
    """
    Task to migrate all instances from the source cloud to the target cloud.
    """

    def execute(self):
        LOG.info('Migrating all instances ...')
	
	ks_source_credentials = getSourceKeystoneCredentials()
	ks_target_credentials = getTargetKeystoneCredentials()
	
	ks_source = getKeystoneClient(**ks_source_credentials)
	ks_target = getKeystoneClient(**ks_target_credentials)

	#Connect to source cloud nova
	invisible_tenantNames = ['invisible_to_admin',
				 'alt_demo',
				 'service']
	
	for tenant in ks_source.tenants.list():
		if tenant.name not in invisible_tenantNames:
			nv_source_credentials = getSourceNovaCredentials()
			nv_target_credentials = getTargetNovaCredentials()
	
			nv_source = getNovaClient(**nv_source_credentials)
			nv_target = getNovaClient(**nv_target_credentials)
	
			#Obtain all instances names per tenant in target cloud 			
			target_instanceNames = []			
			for instance in nv_target.servers.list():
				target_instanceNames.append(instance.name)

			'''
			Check whether the instance from source cloud has existed in the target cloud
			If not, migrate instances into corresponding tenant
			'''
			for instance in nv_source.servers.list():
				if instance.name not in target_instanceNames:
					image = nv_target.images.find(name=nv_source.images.get(instance.image['id']).name)
					image_id = str(image.id)
					flavor = nv_target.flavors.find(name=nv_source.flavors.get(instance.flavor['id']).name)
					nv_target.servers.create(name=instance.name, 
					    		    	 image=image_id, 
							    	 flavor=flavor,
							    	 key_name=instance.key_name,
							    	 security_groups=['default']) #use the security_groups 'default' 
			
	for instance in nv_target.servers.list():
		LOG.debug(instance)
	
