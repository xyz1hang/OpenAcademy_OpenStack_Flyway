import unittest
import sys
sys.path.append('../')

from utils import *

import keystoneclient.v2_0.client
import novaclient.v1_1.client
import glanceclient.v2.client

class TestUtils(unittest.TestCase):
	
	def setUp(self):
		self.username = "admin"
		self.password = "openstack"
		self.auth_url = "http://172.16.45.181:5000/v2.0/"
		self.tenant_name = "admin"
		self.project_id = 'admin'
		self.api_key = 'openstack'
		self.endpoint = "http://172.16.45.181:9292/"

	def test_getKeystoneClient(self):
		
		credentials = {'username': self.username,
			       'password': self.password,
			       'auth_url': self.auth_url,
			       'tenant_name': self.tenant_name}	
		
		ks_client = getKeystoneClient(**credentials)
		self.failUnless(type(ks_client) == keystoneclient.v2_0.client.Client)
	
	def test_getNovaClient(self):
	
		credentials = {'username': self.username,
			       'api_key': self.password,
			       'auth_url': self.auth_url,
			       'project_id': self.project_id}	
		nv_client = getNovaClient(**credentials)
		self.failUnless(type(nv_client) == novaclient.v1_1.client.Client)
	
	def test_getGlanceClient(self):
		
		ks_credentials = {'username': self.username,
			          'password': self.password,
			          'auth_url': self.auth_url,
			          'tenant_name': self.tenant_name}
		
		ks_client = getKeystoneClient(**ks_credentials)
		ks_auth = getAuthenticationRef(ks_credentials)
		ks_token = getToken(ks_auth)
		ks_token_id = getTokenId(ks_token)
		
		gl_credentials = {'version': '1',
			          'endpoint': self.endpoint,
			          'token': ks_token_id}	
		
		gl_client = getGlanceClient(**gl_credentials)
				
		self.failUnless(type(gl_client) == glanceclient.v2.client.Client)
		
if __name__ == '__main__':
    unittest.main()
