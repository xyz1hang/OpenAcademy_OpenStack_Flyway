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
import keystoneclient.v2_0.client as ksclient
from glanceclient import Client as glclient
import novaclient.v1_1.client as nvclient
from common import config as cfg

LOG = logging.getLogger(__name__)

def getKeystoneClient(username=None, password=None, auth_url=None, tenant_name=None, **kwargs):
	"""Get keystone client
	"""
	return ksclient.Client(username=username, password=password,
                               auth_url=auth_url, tenant_name=tenant_name)


def getGlanceClient(version='1', endpoint=None, token=None, **kwargs):
	"""Get glance client
	"""
	return glclient(version=version, endpoint=endpoint, token=token)


def getNovaClient(username=None,api_key=None, auth_url=None, project_id=None, **kwargs):
	"""Get nova client
	"""
	return nvclient.Client(username=username, api_key=api_key,
			       auth_url=auth_url, project_id=project_id)


def getSourceKeystoneCredentials():
	"""Get source cloud keystone credentials
	:rtype dict
	"""
	credentials = {}
	credentials['username'] = cfg.CONF.SOURCE.os_username
        credentials['password'] = cfg.CONF.SOURCE.os_password
        credentials['auth_url'] = cfg.CONF.SOURCE.os_auth_url
        credentials['tenant_name'] = cfg.CONF.SOURCE.os_tenant_name
	return credentials


def getTargetKeystoneCredentials():
	"""Get target cloud keystone credentials
	:rtype dict
	"""
	credentials = {}
	credentials['username'] = cfg.CONF.TARGET.os_username
        credentials['password'] = cfg.CONF.TARGET.os_password
        credentials['auth_url'] = cfg.CONF.TARGET.os_auth_url
        credentials['tenant_name'] = cfg.CONF.TARGET.os_tenant_name
	return credentials


def getSourceGlanceCredentials(token):
	"""Get source glance credentials
	:param token: token id
	:rtype dict
	"""

	credentials = {}
	credentials['version'] = "1"
	credentials['endpoint'] = cfg.CONF.SOURCE.os_endpoint
	credentials['token'] = token
	return credentials


def getTargetGlanceCredentials(token):
	'''Get target glance credentials
	:param token: token id
	:rtype dict
	'''
	credentials = {}
	credentials['version'] = "1"
	credentials['endpoint'] = cfg.CONF.TARGET.os_endpoint
	credentials['token'] = token
	return credentials


def getSourceNovaCredentials():
	"""Get source nova credentials
	:rtype dict
	"""
	credentials = {}
	credentials['username'] = cfg.CONF.SOURCE.os_username
        credentials['api_key'] = cfg.CONF.SOURCE.os_password
        credentials['auth_url'] = cfg.CONF.SOURCE.os_auth_url
        credentials['project_id'] = cfg.CONF.SOURCE.os_tenant_name
	return credentials


def getTargetNovaCredentials():
	"""Get target nova credentials
	:rtype dict
	"""
	credentials = {}
	credentials['username'] = cfg.CONF.TARGET.os_username
        credentials['api_key'] = cfg.CONF.TARGET.os_password
        credentials['auth_url'] = cfg.CONF.TARGET.os_auth_url
        credentials['project_id'] = cfg.CONF.TARGET.os_tenant_name
	return credentials

	
def getAuthenticationRef(credentials):
	"""Get auth ref
	:param credentials: dict
	:rtype dict
	"""
	ks_client = getKeystoneClient(**credentials)
	return ks_client.auth_ref


def getToken(auth_ref):
	"""Get token infos
	:param auth_ref: dict
	"""
	return auth_ref['token']


def getTokenId(token):
	"""Get token id
	"""
	return token['id']

	
def getTenantId(token):
	"""Get tenant id
	:param token: dict
	"""	
	return token['tenant']['id']











