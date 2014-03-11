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
import os

LOG = logging.getLogger(__name__)

class ImageMigrationTask(task.Task):
    """
    Task to migrate all images from the source cloud to the target cloud.
    """
    
    def execute(self):
        LOG.info('Migrating all images ...')

	ks_source_credentials = getSourceKeystoneCredentials()
	ks_target_credentials = getTargetKeystoneCredentials()
	
	ks_source = getKeystoneClient(**ks_source_credentials)
	ks_target = getKeystoneClient(**ks_target_credentials)
	
	ks_source_auth = getAuthenticationRef(ks_source_credentials)
	ks_source_token = getToken(ks_source_auth)
	ks_source_token_id = getTokenId(ks_source_token)
	ks_source_tenant_id = getTenantId(ks_source_token)

	ks_target_auth = getAuthenticationRef(ks_target_credentials)
	ks_target_token = getToken(ks_target_auth)
	ks_target_token_id = getTokenId(ks_target_token)
	ks_target_tenant_id = getTenantId(ks_target_token)
	
	gl_source_credentials = getSourceGlanceCredentials(ks_source_token_id)
	gl_target_credentials = getTargetGlanceCredentials(ks_target_token_id)

	gl_source = getGlanceClient(**gl_source_credentials)	
	gl_target = getGlanceClient(**gl_target_credentials)
	
	target_imageChecksums = []
	for target_image in gl_target.images.list():
		 target_imageChecksums.append(target_image.checksum)
	
	'''
	Find out whether the source cloud image exist in target cloud
	If not, migrate it to target cloud  
	'''
	path = os.getcwd()
	imagedatadir = path+'/.imagedata/'
	if not os.path.exists(imagedatadir):
		os.makedirs(imagedatadir)
	
	for source_image in gl_source.images.list():
		if source_image.checksum not in target_imageChecksums:
			
			image_data = gl_source.images.data(image=source_image.id, do_checksum=True)
						
			with open(imagedatadir+source_image.id,'wb') as f:
				for i in image_data:
					f.write(i)
			
			image = gl_target.images.create(name=source_image.name,
			        			disk_format='qcow2',
			        			container_format='bare',
			        			is_public='True',
							checksum=source_image.checksum,
			        			data=open(imagedatadir+source_image.id,'rb'))
			os.remove(imagedatadir+source_image.id)
	"""		
	for image in gl_target.images.list():
            print 'target:',image.checksum

	for image in gl_source.images.list():
            print 'source:',image.checksum
        """
	
