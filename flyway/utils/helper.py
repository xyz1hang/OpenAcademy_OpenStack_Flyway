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
import random
import smtplib

import keystoneclient.v2_0.client as ksclient
from glanceclient import Client as glclient
import novaclient.v1_1.client as nvclient

from flyway.common import config as cfg

LOG = logging.getLogger(__name__)


def get_keystone_client(username=None, password=None, auth_url=None,
                        tenant_name=None, **kwargs):
    """Get keystone client
    """
    return ksclient.Client(username=username, password=password,
                           auth_url=auth_url, tenant_name=tenant_name)


def get_glance_client(version='1', endpoint=None, token=None, **kwargs):
    """Get glance client
    """
    return glclient(version=version, endpoint=endpoint, token=token)


def get_nova_client(username=None, api_key=None, auth_url=None, project_id=None,
                    **kwargs):
    """Get nova client
    """
    return nvclient.Client(username=username, api_key=api_key,
                           auth_url=auth_url, project_id=project_id)


def get_source_credentials():
    """Get source cloud keystone credentials
    :rtype dict
    """
    credentials = {'username': cfg.CONF.SOURCE.os_username,
                   'password': cfg.CONF.SOURCE.os_password,
                   'auth_url': cfg.CONF.SOURCE.os_auth_url,
                   'tenant_name': cfg.CONF.SOURCE.os_tenant_name}
    return credentials


def get_target_credentials():
    """Get target cloud keystone credentials
    :rtype dict
    """
    credentials = {'username': cfg.CONF.TARGET.os_username,
                   'password': cfg.CONF.TARGET.os_password,
                   'auth_url': cfg.CONF.TARGET.os_auth_url,
                   'tenant_name': cfg.CONF.TARGET.os_tenant_name}
    return credentials


def get_source_glance_credentials(token):
    """Get source glance credentials
    :param token: token id
    :rtype dict
    """
    credentials = {'version': "1",
                   'endpoint': cfg.CONF.SOURCE.os_glance_endpoint,
                   'token': token}
    return credentials


def get_target_glance_credentials(token):
    """Get target glance credentials
    :param token: token id
    :rtype dict
    """
    credentials = {'version': "1",
                   'endpoint': cfg.CONF.TARGET.os_glance_endpoint,
                   'token': token}
    return credentials


class Clients:
    #TODO: attempt to create clients from one place...
    def __init__(self):
        ks_source_credentials = get_source_credentials()
        ks_target_credentials = get_target_credentials()
        ks_source = get_keystone_client(**ks_source_credentials)
        ks_target = get_keystone_client(**ks_target_credentials)

        self.ks_client_source = ksclient.Client(
            token=ks_source.auth_token,
            endpoint=cfg.CONF.SOURCE.os_keystone_endpoint)
        self.ks_client_target = ksclient.Client(
            token=ks_target.auth_token,
            endpoint=cfg.CONF.TARGET.os_keystone_endpoint)

    def get_source(self):
        return self.ks_client_source

    def get_destination(self):
        return self.ks_client_target


def get_clients():
    """function to get a new client for accessing service and
    review token upon expire
    """
    return Clients()


#TODO: Do we actually need this function if we have the
#TODO: keystone client object already
def get_authentication_ref(credentials):
    """Get auth ref
    :param credentials: dict
    :rtype dict
    """
    ks_client = get_keystone_client(**credentials)
    return ks_client.auth_ref


def get_token(auth_ref):
    """Get token infos
    :param auth_ref: dict
    """
    return auth_ref['token']


def get_token_id(token):
    """Get token id
    """
    return token['id']


def get_tenant_id(token):
    """Get tenant id
    :param token: dict
    """
    return token['tenant']['id']


def generate_new_password():
    """Generate a new password containing 10 letters
    """
    letters = 'abcdegfhijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    password = ''
    for i in range(10):
        ranNum = int(random.random() * len(letters))
        password += letters[ranNum]
    return password


def send_email(from_addr, to_addr_list, cc_addr_list, subject, message,
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










