import unittest
import sys
sys.path.append('../flow')

from imagetask import *
from keypairtask import *

cfg.CONF.SOURCE.os_username = "admin"
cfg.CONF.SOURCE.os_password = "openstack"
cfg.CONF.SOURCE.os_auth_url = "http://172.16.45.169:5000/v2.0/"
cfg.CONF.SOURCE.os_tenant_name = "admin"
cfg.CONF.SOURCE.os_endpoint = "http://172.16.45.169:9292"

cfg.CONF.TARGET.os_username = "admin"
cfg.CONF.TARGET.os_password = "openstack"
cfg.CONF.TARGET.os_auth_url = "http://172.16.45.174:5000/v2.0/"
cfg.CONF.TARGET.os_tenant_name = "admin"
cfg.CONF.TARGET.os_endpoint = "http://172.16.45.174:9292"

class TestImageMigration(unittest.TestCase):
	
	#Setup
	def setUp(self):
		self.nv_source_credentials = getSourceNovaCredentials()
		self.nv_target_credentials = getTargetNovaCredentials()
	
		self.nv_source = getNovaClient(**self.nv_source_credentials)
		self.nv_target = getNovaClient(**self.nv_target_credentials)
		
		#Get source cloud keypairs list
		self.source_keypairs = {}
		for keypair in self.nv_source.keypairs.list():
			self.source_keypairs['name'] = keypair.name
			self.source_keypairs['pub_key'] = keypair.public_key
		
		self.target_keypairs = {}
	
	def test_migration_succeed(self):
		"""
		KeypairMigration succeeds after execution of KeypairMigrationTask
		"""	
		#Migrate keypairs
		KeypairMigrationTask('keypair_migration_task').execute()
		
		#Get target cloud keypairs list
		for keypair in self.nv_target.keypairs.list():
			self.target_keypairs['name'] = keypair.name
			self.target_keypairs['pub_key'] = keypair.public_key
		
		#Test should succeed by comparing the source and target keypairs
		self.failUnless(self.source_keypairs==self.target_keypairs)
	
	def test_migration_fail(self):
		"""
		KeypairMigration fails after deleting all the keypairs
		"""	
		#Migrate keypairs
		KeypairMigrationTask('keypair_migration_task').execute()
		
		#Delete all keypairs
		for keypair in self.nv_target.keypairs.list():
			self.nv_target.keypairs.delete(keypair)
		
		#Get target cloud keypairs
		for keypair in self.nv_target.keypairs.list():
			self.target_keypairs['name'] = keypair.name
			self.target_keypairs['pub_key'] = keypair.public_key
		
		#The test should fail by comparing the source and target keypairs	
		self.failIf(self.source_keypairs==self.target_keypairs)

 
if __name__ == '__main__':
    unittest.main()
