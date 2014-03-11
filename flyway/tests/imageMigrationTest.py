import unittest
import sys
sys.path.append('../flow')

from imagetask import *
from utils import *

class TestImageMigration(unittest.TestCase):
	
	#Setup
	def setUp(self):
		self.ks_source_credentials = getSourceKeystoneCredentials()
		self.ks_target_credentials = getTargetKeystoneCredentials()
	
		self.ks_source = getKeystoneClient(**self.ks_source_credentials)
		self.ks_target = getKeystoneClient(**self.ks_target_credentials)
	
		self.ks_source_auth = getAuthenticationRef(self.ks_source_credentials)
		self.ks_source_token = getToken(self.ks_source_auth)
		self.ks_source_token_id = getTokenId(self.ks_source_token)
		self.ks_source_tenant_id = getTenantId(self.ks_source_token)

		self.ks_target_auth = getAuthenticationRef(self.ks_target_credentials)
		self.ks_target_token = getToken(self.ks_target_auth)
		self.ks_target_token_id = getTokenId(self.ks_target_token)
		self.ks_target_tenant_id = getTenantId(self.ks_target_token)
	
		self.gl_source_credentials = getSourceGlanceCredentials(self.ks_source_token_id)
		self.gl_target_credentials = getTargetGlanceCredentials(self.ks_target_token_id)

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
		self.target_images = []
		#Migrate images
		ImageMigrationTask('image_migration_task').execute()
		
		#Get target cloud images list
		for image in self.gl_target.images.list():
			self.target_images.append(image.checksum)
		
		#Test should succeed by comparing the source and target images
		self.failUnless(set(self.source_images).intersection(self.target_images))
		
	def test_migration_fail(self):
		"""ImageMigration fails after deleting all the images
		"""
		self.target_images = []	
		#Migrate images
		ImageMigrationTask('Image_migration_task').execute()
		
		#Delete all images
		for image in self.gl_target.images.list():
			self.gl_target.images.delete(image.id)
		
		#Get target cloud images
		for image in self.gl_target.images.list():
			self.target_images.append(image.checksum)
		print self.source_images
		print self.target_images
		#The test should fail by comparing the source and target images	
		self.failIf(set(self.source_images).intersection(self.target_images))

 
if __name__ == '__main__':
    unittest.main()
