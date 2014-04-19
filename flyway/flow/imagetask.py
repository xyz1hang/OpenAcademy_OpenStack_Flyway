import logging

from glanceclient import exc

from taskflow import task

from utils.db_handlers import images

from utils.db_handlers import tenants
from utils.http_client import HttpRequestHandler
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

        source_glance_server_url = self.gl_source.endpoint
        source_auth_token = self.gl_source.auth_token
        self.s_server_client = HttpRequestHandler(
            source_glance_server_url, source_auth_token)

        target_glance_server_url = self.gl_target.endpoint
        target_auth_token = self.gl_target.auth_token
        self.t_server_client = HttpRequestHandler(
            target_glance_server_url, target_auth_token)

        images.initialise_image_mapping()

    # TODO: all these http request related task can be
    # TODO: restructured into the http_client.py or different modules
    # TODO: each related to one task
    @staticmethod
    def _attr_to_header(image):
        """Convert image object attributes to required HTTP request header
        for using glance REST API.

        :param image: the image object from which the attributes are extracted
        :rtype : A dictionary as HTTP request header for glance API
        """
        supperted_headers = ["name", "id", "store", "disk_format",
                             "properties", "container_format", "size",
                             "checksum", "is_public", "min_ram", "min_disk"]
        header = {}
        for attr in image.__dict__:
            # skip attributes that not supported by the REST API
            if attr not in supperted_headers:
                continue

            if attr is 'properties':
                for sub_attr in getattr(image, attr):
                    header['x-image-meta-property-%s' % sub_attr] = \
                        str(getattr(getattr(image, attr), sub_attr))

            else:
                header['x-image-meta-%s' % attr] = str(getattr(image, attr))

        # don't supply id. Let glance server generate a new
        # id for the image. Avoid handling conflict exception
        if "x-image-meta-id" in header.keys():
            del header['x-image-meta-id']

        return header

    @staticmethod
    def _header_to_attr(header):
        """The reverse operation of attr_to_header()
        Convert HTTP response header to object attributes stored as dictionary

        :param header: a list of key value pair, which stores
        HTTP response message header
        :rtype : image meta data as dictionary
        """
        attributes = {}
        prefix = 'x-image-meta-'
        property_prefix = 'x-image-meta-property-'

        for (key, value) in header:
            if key.startswith(property_prefix):
                sub_attribute = key.replace(property_prefix, '')
                attributes.setdefault('properties', {})
                attributes['properties'].update({sub_attribute: value})
            else:
                attributes[key.replace(prefix, '')] = value
        return attributes

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

        image_migrated = self.gl_target.images.create(
            name=image_meta.name,
            properties=image_meta.properties, size=image_meta.size,
            disk_format=image_meta.disk_format,
            container_format=image_meta.container_format,
            is_public=image_meta.is_public,
            checksum=image_meta.checksum, data=image_data,
            min_ram=image_meta.min_ram, min_disk=image_meta.min_disk,
            owner=owner_target_id)

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
                            "dst_owner_tenant":
                                getattr(m_img_meta, 'owner', 'NULL'),
                            "dst_cloud": cfg.CONF.TARGET.os_cloud_name,
                            "checksum": m_img_meta.checksum}

            # check checksum. If the checksum is not correct
            # it will still be stored in the database in order
            # to be later loaded for further checking (improvement is possible)
            if image_meta.checksum == m_img_meta.checksum:
                dest_details.update({"state": "Completed"})
            else:
                dest_details.update({"state": "Checksum mismatch"})

            logging.debug("Image '%s' upload completed"%image_meta.name)

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
            print "Fail to processing image [Name: '{0}' ID: '{1}']\n" \
                  "Details: {2}".format(image_meta.name,
                                        image_meta.id, str(e))
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
                    print "unable to upload kernel image [Name: '{0}' " \
                          "ID: '{1}'] for image [Name: '{2}' " \
                          "ID: '{3}']".format(image_meta.name, image_meta.id,
                                              image.name, image.id)
                    return None
                # update the corresponding entry in the original
                # image meta_data dictionary
                getattr(image, 'properties')\
                     .update({'kernel_id': new_kernel_id})

            if ramdisk_id:
                image_meta = self.gl_source.images.get(ramdisk_id)
                new_ramdisk_id = self.get_and_upload_img(
                    image_meta, owner_target_id)
                if not new_ramdisk_id:
                    print "unable to upload ramdisk image [Name: '{0}' " \
                          "ID: '{1}'] for image [Name: '{2}' " \
                          "ID: '{3}']".format(image_meta.name, image_meta.id,
                                              image.name, image.id)
                    return None
                # update the corresponding entry in the original
                # image meta_data dictionary
                getattr(image, 'properties')\
                    .update({'ramdisk_id': new_ramdisk_id})

            # upload the image
            new_img_id = self.get_and_upload_img(image, owner_target_id)
            if not new_img_id:
                print "unable to upload image [Name: '{0}' " \
                      "ID: '{1}']".format(image.name, image.id)
                return None

        return new_img_id

    @staticmethod
    def check_image_migrated(image):
        # check whether it has been migrated
        filter_values = [image.name, image.id, image.owner,
                         cfg.CONF.SOURCE.os_cloud_name]
        m_image = images.get_migrated_image(filter_values)
        if m_image and m_image['state'] == 'Completed':
            return True

        return False

    def execute(self, tenant_to_process=None):
        """execute the image migration task

        :param tenant_to_process: list of tenants of which
        all images will be migrated
        """
        images.initialise_image_mapping()

        # migrate all public images
        all_images = self.gl_source.images.list()
        for image in all_images:
            if not image.is_public:
                continue

            # check whether it has been migrated
            if self.check_image_migrated(image):
                continue

            self.migrate_one_image(image, image.owner)

        owner_tenants = tenant_to_process
        if not owner_tenants:
            LOG.info("Migrating images for all tenants...")
            owner_tenants = self.ks_source.tenants.list()

        for tenant in owner_tenants:

            tenant_name = tenant.name
            s_cloud_name = cfg.CONF.SOURCE.os_cloud_name

            LOG.info("Processing tenant '%s'..." % tenant_name)
            filter_values = [tenant.name, s_cloud_name]

            m_tenants = tenants.get_migrated_tenant(filter_values)
            migrated_tenant = m_tenants if m_tenants else None
            if not migrated_tenant:
                print ("Skipping image migration for tenant '%s', since it "
                       "hasn't been migrated yet." % tenant.name)
                continue
            if migrated_tenant['images_migrated']:
                # images already migrated for this tenant
                print ("All images have been migrated for tenant '%s'"
                       % migrated_tenant['project_name'])
                return

            images_to_migrate = \
                self.gl_source.images.list(owner=migrated_tenant['src_uuid'])

            for image in images_to_migrate:
                # check whether it has been migrated
                if self.check_image_migrated(image):
                    continue

                self.migrate_one_image(image, migrated_tenant['dst_uuid'])

                #TODO: update image migration state of corresponding project