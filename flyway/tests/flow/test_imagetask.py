__author__ = 'hydezhang'

from oslo.config import cfg
from glanceclient import exc
from tests.flow.test_base import TestBase
from flow.imagetask import ImageMigrationTask
from common import config
from utils.db_handlers import images


class ImageTaskTest(TestBase):
    """Unit test for Tenant migration"""

    def __init__(self, *args, **kwargs):
        super(ImageTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = ImageMigrationTask('image_migration_task')

    def test_execute(self):
        image_name = "public_image_on_source_cloud"

        image_to_migrate = self.migration_task.gl_source.images.create(
            name=image_name,
            disk_format='qcow2',
            container_format='bare',
            is_public=True,
            location='http://cloud-images.ubuntu.com/releases/12.04.2/release/'
                     'ubuntu-12.04-server-cloudimg-amd64-disk1.img')

        dest_image = None
        try:
            self.migration_task.execute(
                images_to_migrate=[image_to_migrate.id])

            # get the image data that has been migrated from src to dst
            values = [image_name, image_to_migrate.id, image_to_migrate.owner,
                      cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            image_migration_record = images.get_migrated_image(values)
            if not image_migration_record:
                self.assertTrue(False,
                                "No migration detail recorded "
                                "for image '%s'" % image_name)

            dest_id = image_migration_record['dst_uuid']
            dest_image = self.migration_task.gl_target.images.get(dest_id)

            self.assertEqual(image_to_migrate.name, dest_image.name)
            self.assertEqual(image_to_migrate.disk_format,
                             dest_image.disk_format)
            self.assertEqual(image_to_migrate.container_format,
                             dest_image.container_format)
            self.assertEqual(image_to_migrate.is_public,
                             dest_image.is_public)

        except exc.HTTPNotFound as e:
            self.assertTrue(False, e.message)
        except Exception as e:
            self.assertTrue(False, e.message)
        finally:
            self.clean_up(image_to_migrate, dest_image)

    def clean_up(self, image_to_migrate, migrated_image=None):
        self.migration_task.gl_source.images.delete(image_to_migrate)
        # clean database
        filter_values = [image_to_migrate.name,
                         image_to_migrate.id,
                         image_to_migrate.owner,
                         cfg.CONF.SOURCE.os_cloud_name,
                         cfg.CONF.TARGET.os_cloud_name]
        images.delete_migration_record(filter_values)

        if migrated_image:
            self.migration_task.gl_target.images.delete(migrated_image)