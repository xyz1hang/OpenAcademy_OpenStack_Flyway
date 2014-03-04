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

class KeypairMigrationTask(task.Task):
    """
    Task to migrate all keypairs from the source cloud to the target cloud.
    """

    def execute(self):
        LOG.info('Migrating all keypairs ...')
	
	nv_source_credentials = getSourceNovaCredentials()
	nv_target_credentials = getTargetNovaCredentials()
	
	nv_source = getNovaClient(**nv_source_credentials)
	nv_target = getNovaClient(**nv_target_credentials)
	
	'''
	Find out whether the source cloud keypair exist in target cloud
	If not, migrate it to target cloud   
	'''	
	target_keypair_pubs = []
	for keypair in nv_target.keypairs.list():
		target_keypair_pubs.append(keypair.public_key)
	
	for keypair in nv_source.keypairs.list():
		if keypair.public_key not in target_keypair_pubs:
			nv_target.keypairs.create(keypair.name, public_key=keypair.public_key)
			
	for keypair in nv_target.keypairs.list():
	    LOG.debug(keypair)
	
