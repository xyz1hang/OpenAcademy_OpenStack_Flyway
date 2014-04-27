import sys

from glanceclient import exc
from taskflow import task

from utils.db_handlers import images
from utils.db_handlers import tenants
from utils.helper import *
from utils.db_base import *


LOG = logging.getLogger(__name__)


class ImageMigrationTask(task.Task):
    """Task to migrate all images from the source cloud to the target cloud.
        """

    def __init__(self, name, **kwargs):
        super(ImageMigrationTask, self).__init__(name, **kwargs)
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.gl_source = get_glance_source(self.ks_source)
        self.gl_target = get_glance_target(self.ks_target)

        images.initialise_image_mapping()

    def get_image(self, image_id):
        """Fetch image data from glance server directly via http request.

        :rtype : a httplib Response object with image as body
        :param image_id: the uuid of an image
        """
        url = '/v1/images/%s' % image_id
        args = {'headers': {}, 'body': ''}
        resp, body_iter = \
            self.gl_source.images.api.raw_request('GET', url, **args)
        return resp

    def upload_image(self, image_meta, image_data, owner_target_id):
        """Upload an image to target glance server.

        the target cloud
        :param image_meta: metadata of the image as a dictionary
        :param image_data: actual image data
        :param owner_target_id: id of the owner of this image at target cloud

        :rtype : a tuple of (http response headers, http response body)
        """

        supported_headers = ["name", "id", "store", "disk_format", "owner"
                             "properties", "container_format", "size", "data"
                             "checksum", "is_public", "min_ram", "min_disk"]

        img_meta = {}
        for attr in image_meta.__dict__:
            if attr in supported_headers:
                img_meta[attr] = getattr(image_meta, attr)

        img_meta.update({'owner': owner_target_id})
        img_meta.update({'data': image_data})

        image_migrated = self.gl_target.images.create(**img_meta)

        return image_migrated

    def get_and_upload_img(self, image_meta, owner_target_id):
        """Retrieve image from source and upload to
        target server that the http_client points to

        :param image_meta: meta data of the image to be uploaded
        """
        # preparing for database record update
        image_migration_record = \
            {"src_image_name": image_meta.name,
             "src_uuid": image_meta.id,
             "src_owner_uuid": getattr(image_meta, 'owner', 'NULL'),
             "src_cloud": cfg.CONF.SOURCE.os_cloud_name,
             "dst_image_name": 'NULL',
             "dst_uuid": 'NULL',
             "dst_owner_uuid": 'NULL',
             "dst_cloud": 'NULL',
             "checksum": 'NULL',
             "state": "unknown"}

        m_img_meta = None
        try:
            #TODO: how to resolve the owner of the image ?
            #TODO: it could be (the ID of) a tenant or user
            image_data = self.get_image(image_meta.id)

            print ("Uploading image [Name: '{0}', ID: '{1}']..."
                   .format(image_meta.name, image_meta.id))
            m_img_meta = self.upload_image(image_meta, image_data,
                                           owner_target_id)

            # prepare for database record update
            dest_details = {"dst_image_name": m_img_meta.name,
                            "dst_uuid": m_img_meta.id,
                            "dst_owner_uuid": getattr(m_img_meta, 'owner',
                                                        'NULL'),
                            "dst_cloud": cfg.CONF.TARGET.os_cloud_name,
                            "checksum": m_img_meta.checksum}

            # check checksum if provided. If the checksum is not correct
            # it will still be stored in the database in order
            # to be later loaded for further checking
            # (improvement is possible)
            if getattr(image_meta, 'checksum', None):
                if image_meta.checksum == m_img_meta.checksum:
                    dest_details.update({"state": "Completed"})
                else:
                    dest_details.update({"state": "Checksum mismatch"})

            logging.debug("Image '%s' upload completed" % image_meta.name)

        # catch exception thrown by the http_client
        except exc.InvalidEndpoint as e:
            print "Invalid endpoint used to connect to glance server,\n" \
                  "while processing image [Name: '{0}' ID: '{1}']\n" \
                  "Details: {2}".format(image_meta.name,
                                        image_meta.id, str(e))
            dest_details = {"state": "Error"}

        except exc.CommunicationError as e:
            print "Problem communicating with glance server,\n" \
                  "while processing image [Name: '{0}' ID: '{1}']\n" \
                  "Details: {2}".format(image_meta.name,
                                        image_meta.id, str(e))
            dest_details = {"state": "Error"}

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            details = str(str(exc_type) + ": " + e.message
                          + " [line: " + str(exc_tb.tb_lineno) + "]")
            print "Fail to processing image [Name: '{0}' ID: '{1}']\n" \
                  "Details: {2}".format(image_meta.name,
                                        image_meta.id, details)
            dest_details = {"state": "Error"}

        image_migration_record.update(dest_details)

        # update database record
        images.record_image_migrated([image_migration_record])

        return m_img_meta.id if m_img_meta else None

    def migrate_one_image(self, image, owner_target_id):

        new_img_id = None
        if image.status == "active":
            LOG.info('Migrating image [ID: %s] ...' % image.id)

            # upload kernel image and ramdisk image first if exists
            kernel_id = getattr(image, 'properties', {}).get('kernel_id')
            ramdisk_id = getattr(image, 'properties', {}).get('ramdisk_id')

            if kernel_id:
                image_meta = self.gl_source.images.get(kernel_id)
                new_kernel_id = self.get_and_upload_img(
                    image_meta, owner_target_id)
                if not new_kernel_id:
                    print "Unable to upload kernel image [Name: '{0}' " \
                          "ID: '{1}'] for image [Name: '{2}' " \
                          "ID: '{3}']".format(image_meta.name, image_meta.id,
                                              image.name, image.id)
                    return None
                # update the corresponding entry in the original
                # image meta_data dictionary
                getattr(image, 'properties') \
                    .update({'kernel_id': new_kernel_id})

            if ramdisk_id:
                image_meta = self.gl_source.images.get(ramdisk_id)
                new_ramdisk_id = self.get_and_upload_img(
                    image_meta, owner_target_id)
                if not new_ramdisk_id:
                    print "Unable to upload ramdisk image [Name: '{0}' " \
                          "ID: '{1}'] for image [Name: '{2}' " \
                          "ID: '{3}']".format(image_meta.name, image_meta.id,
                                              image.name, image.id)
                    return None
                # update the corresponding entry in the original
                # image meta_data dictionary
                getattr(image, 'properties') \
                    .update({'ramdisk_id': new_ramdisk_id})

            # upload the image
            new_img_id = self.get_and_upload_img(image, owner_target_id)
            if not new_img_id:
                print "Unable to upload image [Name: '{0}' " \
                      "ID: '{1}']".format(image.name, image.id)
                return None

        return new_img_id

    @staticmethod
    def check_image_migrated(image):
        # check whether it has been migrated
        filter_values = [image.name, image.id, image.owner,
                         cfg.CONF.SOURCE.os_cloud_name,
                         cfg.CONF.TARGET.os_cloud_name]
        m_image = images.get_migrated_image(filter_values)
        if m_image and m_image['state'] == 'Completed':
            return True

        return False

    def execute(self, images_to_migrate, tenant_to_process):
        """execute the image migration task

        :param tenant_to_process: list of tenants of which
        all images will be migrated
        :param images_to_migrate: list of IDs of images to be migrated
        """

        images_to_move = []

        # migrate given images
        if images_to_migrate:
            for img_id in images_to_migrate:
                try:
                    img = self.gl_source.images.get(img_id)
                    img_owner_pair = {'img': img,
                                      'owner': getattr(img, 'owner', None)}
                    images_to_move.append(dict(img_owner_pair))

                except exc.HTTPNotFound:
                    print ("Can not find image of id: '{0}' on cloud '{1}'"
                           .format(img_id, cfg.CONF.SOURCE.os_cloud_name))

        # migrate images from given tenants or all images
        else:
            owner_tenants = tenant_to_process
            if not owner_tenants:
                owner_tenants = []
                LOG.info("Migrating images for all tenants...")
                for tenant in self.ks_source.tenants.list():
                    owner_tenants.append(tenant.name)

            # migrate all public images
            all_images = self.gl_source.images.list()
            for image in all_images:
                if not image.is_public:
                    continue

                # check whether it has been migrated
                if self.check_image_migrated(image):
                    continue

                img_owner_pair = {'img': image, 'owner': None}
                images_to_move.append(dict(img_owner_pair))

            # migrate images owned by tenants
            for tenant_name in owner_tenants:

                s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
                t_cloud_name = cfg.CONF.TARGET.os_cloud_name

                LOG.info("Processing tenant '%s'..." % tenant_name)
                filter_values = [tenant_name, s_cloud_name, t_cloud_name]

                m_tenants = tenants.get_migrated_tenant(filter_values)
                migrated_tenant = m_tenants if m_tenants else None
                if not migrated_tenant:
                    print ("Skipping image migration for tenant '%s', "
                           "since it has no migration record." % tenant_name)
                    continue
                if migrated_tenant['images_migrated']:
                    # images already migrated for this tenant
                    print ("All images have been migrated for tenant '%s'"
                           % migrated_tenant['project_name'])
                    return

                owned_images = self.gl_source.images.list(
                    owner=migrated_tenant['src_uuid'])
                for img in owned_images:
                    img_owner_pair = {'img': img,
                                      'owner': migrated_tenant['dst_uuid']}
                    images_to_move.append(dict(img_owner_pair))

        for image_owner_pair in images_to_move:
            # check whether it has been migrated
            if self.check_image_migrated(image_owner_pair['img']):
                print ("image [Name: '{0}', ID: '{1}' has been migrated"
                       .format(image_owner_pair['img'].name,
                               image_owner_pair['img'].id))
                continue

            self.migrate_one_image(image_owner_pair['img'],
                                   image_owner_pair['owner'])

            #TODO: update image migration state of corresponding project