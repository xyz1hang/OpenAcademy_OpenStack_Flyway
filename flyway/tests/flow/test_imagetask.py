__author__ = 'hydezhang'

from oslo.config import cfg
from glanceclient import exc
from tests.flow.test_base import TestBase
from flow.imagetask import ImageMigrationTask
from common import config
from utils.db_handlers import images

# testing inputs
owner_target_id = '2ddc4b6528f24b039cf4ec093ae8a214'
image_name = "public_image_on_source_cloud"


class ImageTaskTest(TestBase):
    """Unit test for Tenant migration"""

    def __init__(self, *args, **kwargs):
        super(ImageTaskTest, self).__init__(*args, **kwargs)
        self.migration_task = ImageMigrationTask('image_migration_task')
        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        self.image_id = 'cce60962-c008-46ed-919d-b003f7c78ea2'

    def create_images(self):

        image_to_migrate = self.migration_task.gl_source.images.create(
            name=image_name,
            disk_format='qcow2',
            container_format='bare',
            is_public=True,
            location='http://cloud-images.ubuntu.com/releases/12.04.2/release/'
                     'ubuntu-12.04-server-cloudimg-amd64-disk1.img')
        self.image_id = image_to_migrate.id
        return image_to_migrate

    def test_check_image_migrated(self):
        # migrate an image, manually check if it is correctly migrated
        image_to_migrate = self.create_images()
        image = self.migration_task.gl_source.images.get(self.image_id)
        self.migration_task.migrate_one_image(image, owner_target_id)

         # get the image data that has been migrated from src to dst
        filters = {"src_image_name": image_name,
                   "src_uuid": image_to_migrate.id,
                   "src_cloud": self.s_cloud_name,
                   "dst_cloud": self.t_cloud_name}

        image_migration_record = images.get_migrated_image(filters)

        if not image_migration_record:
                self.assertTrue(False,
                                "No migration detail recorded "
                                "for image '%s'" % image_name)

        m_image = image_migration_record[0] \
            if image_migration_record else None
        dest_id = m_image['dst_uuid']
        dest_image = self.migration_task.gl_target.images.get(dest_id)

        self.assertEqual(image_to_migrate.name, dest_image.name)
        self.assertEqual(image_to_migrate.disk_format,
                         dest_image.disk_format)
        self.assertEqual(image_to_migrate.container_format,
                         dest_image.container_format)
        self.assertEqual(image_to_migrate.is_public, dest_image.is_public)
       # self.clean_up(image_to_migrate, dest_image)
        # test check_image_migrated
        result = self.migration_task.check_image_migrated(image)
        print result
        self.assertTrue(result)
        self.clean_up(image_to_migrate, dest_image)

    def test_get_image(self):
        print self.migration_task.get_image(self.image_id)

    def test_upload_image(self):
        image_to_migrate = self.create_images()

        image_meta = self.migration_task.gl_source.images.get(self.image_id)
        image_data = self.migration_task.get_image(image_meta.id)
        dest_image = self.migration_task.upload_image(image_meta,
                                                      image_data, owner_target_id)

        self.assertEqual(image_to_migrate.name, dest_image.name)
        self.assertEqual(image_to_migrate.disk_format,
                         dest_image.disk_format)
        self.assertEqual(image_to_migrate.container_format,
                         dest_image.container_format)
        self.assertEqual(image_to_migrate.is_public, dest_image.is_public)
        self.clean_up(image_to_migrate, dest_image)

    def test_get_and_upload_img(self):
        image_to_migrate = self.create_images()
        image_meta = self.migration_task.gl_source.images.get(self.image_id)
        self.migration_task.get_and_upload_img(image_meta, owner_target_id)

        # get the image data that has been migrated from src to dst
        filters = {"src_image_name": image_name,
                   "src_uuid": image_to_migrate.id,
                   "src_cloud": self.s_cloud_name,
                   "dst_cloud": self.t_cloud_name}

        image_migration_record = images.get_migrated_image(filters)

        if not image_migration_record:
                self.assertTrue(False,
                                "No migration detail recorded "
                                "for image '%s'" % image_name)

        m_image = image_migration_record[0] \
            if image_migration_record else None
        dest_id = m_image['dst_uuid']
        dest_image = self.migration_task.gl_target.images.get(dest_id)

        self.assertEqual(image_to_migrate.name, dest_image.name)
        self.assertEqual(image_to_migrate.disk_format,
                         dest_image.disk_format)
        self.assertEqual(image_to_migrate.container_format,
                         dest_image.container_format)
        self.assertEqual(image_to_migrate.is_public, dest_image.is_public)
        self.clean_up(image_to_migrate, dest_image)

    def test_migrate_one_image(self):
        image_to_migrate = self.create_images()
        image = self.migration_task.gl_source.images.get(self.image_id)
        self.migration_task.migrate_one_image(image, owner_target_id)

         # get the image data that has been migrated from src to dst
        filters = {"src_image_name": image_name,
                   "src_uuid": image_to_migrate.id,
                   "src_cloud": self.s_cloud_name,
                   "dst_cloud": self.t_cloud_name}

        image_migration_record = images.get_migrated_image(filters)

        if not image_migration_record:
                self.assertTrue(False,
                                "No migration detail recorded "
                                "for image '%s'" % image_name)

        m_image = image_migration_record[0] \
            if image_migration_record else None
        dest_id = m_image['dst_uuid']
        dest_image = self.migration_task.gl_target.images.get(dest_id)

        self.assertEqual(image_to_migrate.name, dest_image.name)
        self.assertEqual(image_to_migrate.disk_format,
                         dest_image.disk_format)
        self.assertEqual(image_to_migrate.container_format,
                         dest_image.container_format)
        self.assertEqual(image_to_migrate.is_public, dest_image.is_public)
        self.clean_up(image_to_migrate, dest_image)

    def test_execute(self):
        image_to_migrate = self.create_images()

        dest_image = None
        try:
            self.migration_task.execute(
                images_to_migrate=[image_to_migrate.id], tenant_to_process=None)

            # get the image data that has been migrated from src to dst
            filters = {"src_image_name": image_name,
                       "src_uuid": image_to_migrate.id,
                       "src_cloud": self.s_cloud_name,
                       "dst_cloud": self.t_cloud_name}

            image_migration_record = images.get_migrated_image(filters)
            if not image_migration_record:
                self.assertTrue(False,
                                "No migration detail recorded "
                                "for image '%s'" % image_name)
            m_image = image_migration_record[0] \
                if image_migration_record else None
            dest_id = m_image['dst_uuid']
            dest_image = self.migration_task.gl_target.images.get(dest_id)

            self.assertEqual(image_to_migrate.name, dest_image.name)
            self.assertEqual(image_to_migrate.disk_format,
                             dest_image.disk_format)
            self.assertEqual(image_to_migrate.container_format,
                             dest_image.container_format)
            self.assertEqual(image_to_migrate.is_public,
                             dest_image.is_public)

            image = self.migration_task.gl_source.images.get(self.image_id)

            result = self.migration_task.check_image_migrated(image)
            print result
            self.assertTrue(result)

        except exc.HTTPNotFound as e:
            self.assertTrue(False, e.message)
        except Exception as e:
            self.assertTrue(False, e.message)
        finally:
            print 'finished'
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



