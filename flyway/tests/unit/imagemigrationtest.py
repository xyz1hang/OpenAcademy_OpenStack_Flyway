import unittest
from flow import imagetask

class TestImageMigration(unittest.TestCase):

	def setUp(self):
		pass
	
	def testImages(self):
		ImageMigrationTask('image_migration_task').execute()
		#self.assertEqual()

 
if __name__ == '__main__':
    unittest.main()
