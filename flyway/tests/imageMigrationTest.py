import unittest
import sys
sys.path.append('../flow')

from imagetask import *
from utils import *

class TestImageMigration(unittest.TestCase):
	
	#Setup
	def setUp(self):
		self.username = "admin"
		self.password = "openstack"
		self.source_auth_url = "http://172.16.45.181:5000/v2.0/"
		self.target_auth_url = "http://172.16.45.182:5000/v2.0/"
		self.tenant_name = "admin"
		self.source_endpoint = "http://172.16.45.181:9292/"
		self.target_endpoint = "http://172.16.45.182:9292/"

		self.ks_source_credentials = {'username': self.username,
			       		      'password': self.password,
			       		      'auth_url': self.source_auth_url,
			                      'tenant_name': self.tenant_name}	
		
		self.ks_target_credentials = {'username': self.username,
			       		      'password': self.password,
			       		      'auth_url': self.target_auth_url,
			                      'tenant_name': self.tenant_name}	
	
		self.ks_source = getKeystoneClient(**self.ks_source_credentials)
		self.ks_target = getKeystoneClient(**self.ks_target_credentials)
	
		self.ks_source_auth = getAuthenticationRef(self.ks_source_credentials)
		self.ks_source_token = getToken(self.ks_source_auth)
		self.ks_source_token_id = getTokenId(self.ks_source_token)
		
		self.ks_target_auth = getAuthenticationRef(self.ks_target_credentials)
		self.ks_target_token = getToken(self.ks_target_auth)
		self.ks_target_token_id = getTokenId(self.ks_target_token)
		
		self.gl_source_credentials = {'version':'1',
					      'endpoint': self.source_endpoint,
					      'token': self.ks_source_token_id}

		self.gl_target_credentials = {'version':'1',
					      'endpoint': self.target_endpoint,
					      'token': self.ks_target_token_id}

		self.gl_source = getGlanceClient(**self.gl_source_credentials)	
		self.gl_target = getGlanceClient(**self.gl_target_credentials)
		
		#Get source cloud images list
		self.source_images = []
		for image in self.gl_source.images.list():
			self.source_images.append(image.checksum)
		
		self.target_images = []
	
	def test_migration_succeed(self):
		"""ImageMigration succeeds after execution of ImageMigrationTask
		"""	
		#Delete all images
		for image in self.gl_target.images.list():
			self.gl_target.images.delete(image.id)

		#Migrate images
		ImageMigrationTask('image_migration_task').execute()
		
		#Get target cloud images list
		for image in self.gl_target.images.list():
			self.target_images.append(image.checksum)
		
		#Test should succeed by comparing the source and target images
		self.failUnless(set(self.source_images)==set(self.target_images))
		
	def test_migration_fail(self):
		"""Test there is no duplicates of images
		"""
		#Delete all images
		for image in self.gl_target.images.list():
			self.gl_target.images.delete(image.id)

		#Migrate images
		ImageMigrationTask('image_migration_task').execute()

		#Migrate images
		ImageMigrationTask('image_migration_task').execute()
		
		#Get target cloud images list
		for image in self.gl_target.images.list():
			self.target_images.append(image.checksum)
		
		#Test should succeed by comparing the source and target images
		self.failIf(set(self.source_images)!=set(self.target_images))
 
if __name__ == '__main__':
    unittest.main()
