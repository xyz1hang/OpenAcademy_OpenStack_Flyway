import logging


import sys
sys.path.append("../../flyway")

import keystoneclient.v2_0.client as ksclient
from glanceclient import Client as glclient
import novaclient.v1_1.client as nvclient

from flyway.common import config as cfg

LOG = logging.getLogger(__name__)

class Clients(object):

    def __init__(self):
        super(Clients, self).__init__()

    def get_keystone_source(self):
        """Get source keystone client
        """
        ks_source_credentials = self._get_keystone_source_credentials()

        ks_source = self._get_keystone_client(**ks_source_credentials)
        ks_client_source = ksclient.Client(token=ks_source.auth_token,
                                           endpoint=cfg.CONF.SOURCE.os_keystone_endpoint)
        return ks_client_source


    def get_keystone_target(self):
        """Get target keystone client
        """
        ks_target_credentials = self._get_keystone_target_credentials()
        ks_target = self._get_keystone_client(**ks_target_credentials)
        ks_client_target = ksclient.Client(token=ks_target.auth_token,
                                           endpoint=cfg.CONF.TARGET.os_keystone_endpoint)
        return ks_client_target



    def get_glance_source(self):
        """Get source glance client
        """
        ks_source = self.get_keystone_source()
        gl_source_credentials = self._get_glance_source_credentials(ks_source.auth_token)
        return self._get_glance_client(**gl_source_credentials)


    def get_glance_target(self):
        """Get target glance client
        """
        ks_target = self.get_keystone_target()
        gl_target_credentials = self._get_glance_target_credentials(ks_target.auth_token)
        return self._get_glance_client(**gl_target_credentials)


    def get_nova_source(self):
        """Get source nova client
        """
        nv_source_credentials = self._get_nova_source_credentials()
        return self._get_nova_client(**nv_source_credentials)


    def get_nova_target(self):
        """Get target nova client
        """
        nv_target_credentials = self._get_nova_target_credentials()
        return self._get_nova_client(**nv_target_credentials)


    def _get_keystone_client(self, username=None, password=None, auth_url=None,
                             tenant_name=None, **kwargs):
        """Get keystone client
        """
        return ksclient.Client(username=username, password=password,
                               auth_url=auth_url, tenant_name=tenant_name)


    def _get_glance_client(self, version='1', endpoint=None, token=None, **kwargs):
        """Get glance client
        """
        return glclient(version=version, endpoint=endpoint, token=token)


    def _get_nova_client(self, username=None, api_key=None, auth_url=None, project_id=None, **kwargs):
        """Get nova client
        """
        return nvclient.Client(username=username, api_key=api_key,
                               auth_url=auth_url, project_id=project_id)


    def _get_keystone_source_credentials(self):
        """Get source cloud keystone credentials
        :rtype dict
        """
        credentials = {'username': cfg.CONF.SOURCE.os_username,
                       'password': cfg.CONF.SOURCE.os_password,
                       'auth_url': cfg.CONF.SOURCE.os_auth_url,
                       'tenant_name': cfg.CONF.SOURCE.os_tenant_name}
        return credentials


    def _get_keystone_target_credentials(self):
        """Get target cloud keystone credentials
        :rtype dict
        """
        credentials = {'username': cfg.CONF.TARGET.os_username,
                       'password': cfg.CONF.TARGET.os_password,
                       'auth_url': cfg.CONF.TARGET.os_auth_url,
                       'tenant_name': cfg.CONF.TARGET.os_tenant_name}
        return credentials


    def _get_glance_source_credentials(self, token):
        """Get source glance credentials
        :param token: token id
        :rtype dict
        """
        credentials = {'version': "1",
                       'endpoint': cfg.CONF.SOURCE.os_glance_endpoint,
                       'token': token}
        return credentials


    def _get_glance_target_credentials(self, token):
        """Get target glance credentials
        :param token: token id
        :rtype dict
        """
        credentials = {'version': "1",
                       'endpoint': cfg.CONF.TARGET.os_glance_endpoint,
                       'token': token}
        return credentials


    def _get_nova_source_credentials(self):
        """Get source nova credentials
        :rtype dict
        """

        credentials = {'username':cfg.CONF.SOURCE.os_username,
                       'api_key':cfg.CONF.SOURCE.os_password,
                       'auth_url':cfg.CONF.SOURCE.os_auth_url,
                       'project_id':cfg.CONF.SOURCE.os_tenant_name}

        return credentials


    def _get_nova_target_credentials(self):
        """Get target nova credentials
        :rtype dict
        """
        credentials = {'username':cfg.CONF.TARGET.os_username,
                       'api_key':cfg.CONF.TARGET.os_password,
                       'auth_url':cfg.CONF.TARGET.os_auth_url,
                       'project_id':cfg.CONF.TARGET.os_tenant_name}

        return credentials



















