import sys
from taskflow import task

sys.path.append('../')

from flyway.utils.helper import *
import os

LOG = logging.getLogger(__name__)


class ImageMigrationTask(task.Task):
    """
    Task to migrate all images from the source cloud to the target cloud.
    """

    def execute(self):
        """
        Find out whether the source cloud image exist in target cloud
        If not, migrate it to target cloud
        """
        LOG.info('Migrating all images ...')

        ks_source_credentials = get_source_credentials()
        ks_target_credentials = get_target_credentials()

        ks_source = get_keystone_client(**ks_source_credentials)
        ks_target = get_keystone_client(**ks_target_credentials)

        ks_source_auth = get_authentication_ref(ks_source_credentials)
        ks_source_token = get_token(ks_source_auth)
        ks_source_token_id = get_token_id(ks_source_token)
        ks_source_tenant_id = get_tenant_id(ks_source_token)

        ks_target_auth = get_authentication_ref(ks_target_credentials)
        ks_target_token = get_token(ks_target_auth)
        ks_target_token_id = get_token_id(ks_target_token)
        ks_target_tenant_id = get_tenant_id(ks_target_token)

        gl_source_credentials = get_source_glance_credentials(ks_source_token_id)
        gl_target_credentials = get_target_glance_credentials(ks_target_token_id)

        gl_source = get_glance_client(**gl_source_credentials)
        gl_target = get_glance_client(**gl_target_credentials)

        target_imageChecksums = []
        for target_image in gl_target.images.list():
            target_imageChecksums.append(target_image.checksum)

        path = os.getcwd()
        imagedatadir = path + '/.imagedata/'
        if not os.path.exists(imagedatadir):
            os.makedirs(imagedatadir)

        for source_image in gl_source.images.list():
            if source_image.checksum not in target_imageChecksums:

                image_data = gl_source.images.data(image=source_image.id,
                                                   do_checksum=True)

                with open(imagedatadir + source_image.id, 'wb') as f:
                    for i in image_data:
                        f.write(i)

                image = gl_target.images.create(name=source_image.name,
                                                disk_format='qcow2',
                                                container_format='bare',
                                                is_public='True',
                                                checksum=source_image.checksum,
                                                data=open(
                                                    imagedatadir + source_image.id,
                                                    'rb'))
                os.remove(imagedatadir + source_image.id)

        """for image in gl_target.images.list():
                print 'target:',image.checksum
           for image in gl_source.images.list():
                print 'source:',image.checksum"""