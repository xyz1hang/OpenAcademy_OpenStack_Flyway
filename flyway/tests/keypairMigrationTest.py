import unittest
import sys
sys.path.append('../flow')

from keypairtask import *
from utils import *

class TestKeypairMigration(unittest.TestCase):
	
	#Setup
	def setUp(self):
		self.nv_source_credentials = getSourceNovaCredentials()
		self.nv_target_credentials = getTargetNovaCredentials()
	
		self.nv_source = getNovaClient(**self.nv_source_credentials)
		self.nv_target = getNovaClient(**self.nv_target_credentials)
		
		#Get source cloud keypairs list
		self.source_keypairs = []
		for keypair in self.nv_source.keypairs.list():
			self.source_keypairs.append(keypair.public_key)
		
		self.target_keypairs = []
	
	def test_migration_succeed(self):
		"""KeypairMigration succeeds after execution of KeypairMigrationTask
		"""	
		#Delete all keypairs
		for keypair in self.nv_target.keypairs.list():
			self.nv_target.keypairs.delete(keypair.id)

		#Migrate keypairs
		KeypairMigrationTask('keypair_migration_task').execute()
		
		#Get target cloud keypairs list
		for keypair in self.nv_target.keypairs.list():
			self.target_keypairs.append(keypair.public_key)
		
		#Test should succeed by comparing the source and target keypairs
		self.failUnless(set(self.source_keypairs)==set(self.target_keypairs))
	
		
	def test_migration_fail(self):
		"""Test there is no duplicates of keypairs
		"""	
		#Delete all keypairs
		for keypair in self.nv_target.keypairs.list():
			self.nv_target.keypairs.delete(keypair.id)

		#Migrate keypairs
		KeypairMigrationTask('keypair_migration_task').execute()

		#Migrate keypairs
		KeypairMigrationTask('keypair_migration_task').execute()
		
		#Get target cloud keypairs
		for keypair in self.nv_target.keypairs.list():
			self.target_keypairs.append(keypair.public_key)
		
		#The test should fail by comparing the source and target keypairs	
		self.failIf(set(self.source_keypairs)!=set(self.target_keypairs))
	
 
if __name__ == '__main__':
    unittest.main()
