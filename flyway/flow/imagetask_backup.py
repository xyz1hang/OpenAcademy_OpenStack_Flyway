import logging

import sys
sys.path.append('../')

from taskflow import task
from utils.helper import *
from utils.db_base import *
import time
import os

LOG = logging.getLogger(__name__)


class ImageMigrationTask(task.Task):
        """Task to migrate all images from the source cloud to the target cloud.
        """

        def __init__(self, *args, **kwargs):
            super(ImageMigrationTask, self).__init__(**kwargs)
            self.gl_source = get_glance_source()
            self.gl_target = get_glance_target()

            self.target_image_checksums = []
            for target_image in self.gl_target.images.list():
                    self.target_image_checksums.append(target_image.checksum)

            path = os.getcwd()
            self.imagedatadir = path + '/.imagedata/'
            if not os.path.exists(self.imagedatadir):
                os.makedirs(self.imagedatadir)

            self.initialise_db()

        def migrate_one_image(self, image):
            if image.checksum not in self.target_image_checksums:
                image_data = self.gl_source.images.data(image=image.id,
                                                        do_checksum=True)

                with open(self.imagedatadir + image.id, 'wb') as f:
                    for chunk in image_data:
                        f.write(chunk)

                image = self.gl_target.images.create(name=image.name,
                                                     disk_format=image.disk_format,
                                                     container_format=image.container_format,
                                                     is_public=image.is_public,
                                                     checksum=image.checksum,
                                                     data=open(self.imagedatadir + image.id,'rb'))

                set_dict = {'completed':'YES'}
                where_dict = {'name': image.name}
                start = time.time()
                while True:
                   if time.time() - start > 10:
                            print 'Fail!!!'
                            break
                   elif self.migration_succeed(image):
                            update_table('images', set_dict, where_dict, False)
                            break
                #os.remove(self.imagedatadir + image.id)

        def migration_succeed(self, image):
            for target_image in self.gl_target.images.list():
                if image.checksum == target_image.checksum:
                    if image.status == 'active':
                        return True

            return False

        def initialise_db(self):
            table_columns = '''id INT NOT NULL AUTO_INCREMENT,
                               name VARCHAR(64) NOT NULL,
                               checksum VARCHAR(1024) NOT NULL,
                               completed VARCHAR(10),
                               PRIMARY KEY(id)
                            '''

            if not check_table_exist('images'):
                    create_table('images', table_columns, False)

            values = []
            for image in self.gl_source.images.list():
                if image.checksum not in self.target_image_checksums:
                    values.append("null, '{0}', '{1}', 'NO'".format(image.name, image.checksum))

            insert_record('images', values, False)

        def execute(self):
            """Find out whether the source cloud image exist in target cloud
            If not, migrate it to target cloud
            """
            LOG.info('Migrating all images ...')

            for image in self.gl_source.images.list():
                    self.migrate_one_image(image)