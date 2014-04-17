import json
import logging

from taskflow import task

from utils.db_handlers import images
from utils.db_handlers import tenants
from utils.http_client import HttpRequestHandler
from utils.exceptions import HttpRequestException
from utils.helper import *
from utils.db_base import *


LOG = logging.getLogger(__name__)


class ImageMigrationTask(task.Task):
    """Task to migrate all images from the source cloud to the target cloud.
        """

    def __init__(self, **kwargs):
        super(ImageMigrationTask, self).__init__(**kwargs)
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
        header = {}
        for attr in image.__dict__:
            if attr is 'properties':
                for sub_attr in image[attr]:
                    header['x-image-meta-property-%s' % sub_attr] = \
                        image[attr][sub_attr]

            else:
                header['x-image-meta-%s' % attr] = image[attr]

        # don't supply id. Let glance server generate a new
        # id for the image. Avoid handling conflict exception
        if "x-image-meta-id" in header.keys():
            del header['x-image-meta-id']

        return header

    @staticmethod
    def _header_to_attr(header):
        """The reverse operation of attr_to_header()
        Convert HTTP response header to object attributes dictionary

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

    @staticmethod
    def _check_upload_response(header, body):
        """Check that the headers of an upload are reasonable.

        :param header: the header of the response message
        :param body: the body of the response message
        """

        if 'status' not in header:
            try:
                msg_body = json.loads(body)
                if 'image' in msg_body and 'status' in msg_body['image']:
                    return

            except:
                raise Exception('Error uploading image: %s' % body)

    @staticmethod
    def get_image(image_id, http_client):
        """Fetch image data from glance server directly via http request.

        :rtype : a httplib Response object with image as body
        :param image_id: the uuid of an image
        """
        url = '/v1/images/%s' % image_id
        return http_client.send_request('GET', url, {}, '')

    def upload_image(self, http_client, image_meta, image_data):
        """Upload an image to target glance server.

        :param http_client: the http client that handles http request for
        the target cloud
        :param image_meta: metadata of the image as a dictionary
        :param image_data: actual image data

        :rtype : a tuple of (http response headers, http response body)
        """

        url = '/v1/images'
        headers = self._attr_to_header(image_meta)
        headers['Content-Type'] = 'application/octet-stream'
        headers['Content-Length'] = int(image_meta['size'])

        response = http_client.send_request('POST', url, headers, image_data)
        headers = self._header_to_attr(response.getheaders())

        logging.debug('Image upload completed')
        body = response.read()
        return headers, body

    def get_and_upload_img(self, image_meta, http_client):
        """Retrieve image from source and upload to
        target server that the http_client points to

        :param image_meta: meta data of the image to be uploaded
        :param http_client: the http client point to target glance server
        """
        # preparing for database record update
        image_migration_record = \
            {"src_image_name": image_meta['name'],
             "src_uuid": image_meta['id'],
             "src_owner_tenant": image_meta.get('owner', 'NULL'),
             "src_cloud": cfg.CONF.SOURCE.os_cloud_name,
             "dst_image_name": 'NULL',
             "dst_uuid": 'NULL',
             "dst_owner_tenant": 'NULL',
             "dst_cloud": 'NULL',
             "checksum": 'NULL',
             "state": "unknown"}

        migrated_image_meta = {}

        try:
            #TODO: how to resolve the owner of the image ?
            #TODO: it could be (the ID of) a tenant or user
            image_data = self.get_image(image_meta['id'], http_client)
            headers, body = self.upload_image(
                http_client, image_meta, image_data)
            migrated_image_meta = headers
            self._check_upload_response(headers, body)

            # prepare for database record update
            dest_details = {"dst_image_name": headers['name'],
                            "dst_uuid": headers['id'],
                            "dst_owner_tenant": headers.get('owner', 'NULL'),
                            "dst_cloud": cfg.CONF.TARGET.os_cloud_name,
                            "checksum": headers['checksum']}

            # check checksum. If the checksum is not correct
            # it will still be stored in the database in order
            # to be later loaded for further checking (improvement is possible)
            if image_meta['checksum'] == headers['checksum']:
                dest_details.update({"state": "Completed"})
            else:
                dest_details.update({"state": "Checksum mismatch"})

        # catch exception thrown by the http_client
        except HttpRequestException as e:
            print "Problem communicating with glance server, " \
                  "while processing image [Name: {0} ID: {1}]\n" \
                  "Details: {3}".format(image_meta['name'],
                                        image_meta['id'], e)
            dest_details = {"state": "Error"}

        image_migration_record.update(dest_details)

        # update database record
        images.record_image_migrated(**image_migration_record)

        return migrated_image_meta['id']

    def migrate_one_image(self, image):

        new_img_id = None
        if image['status'] is "active":
            LOG.info('Migrating image [ID: %s] ...' % image['id'])

            # upload kernel image and ramdisk image first if exists
            kernel_id = image.get('properties', {}).get('kernel_id')
            ramdisk_id = image.get('properties', {}).get('ramdisk_id')

            if kernel_id:
                image_meta = self.gl_source.images.get(kernel_id)
                new_kernel_id = self.get_and_upload_img(
                    image_meta, self.s_server_client)
                # update the corresponding entry in the original
                # image meta_data dictionary
                new_prop = image.get('properties') \
                    .update({'kernel_id': new_kernel_id})
                image.update({'properties': new_prop})

            if ramdisk_id:
                image_meta = self.gl_source.images.get(ramdisk_id)
                new_ramdisk_id = self.get_and_upload_img(
                    image_meta, self.s_server_client)
                # update the corresponding entry in the original
                # image meta_data dictionary
                new_prop = image.get('properties') \
                    .update({'ramdisk_id': new_ramdisk_id})
                image.update({'properties': new_prop})

            # upload the image
            new_img_id = self.get_and_upload_img(
                image, self.s_server_client)

        return new_img_id

    def execute(self, tenant_to_process=None):
        """execute the image migration task

        :param tenant_to_process: list of tenants of which
        all images will be migrated
        """
        images.initialise_image_mapping()

        owner_tenants = tenant_to_process
        if not owner_tenants:
            LOG.info("Migrating images for all tenants...")
            owner_tenants = self.ks_source.tenants.list()

        for tenant in owner_tenants:
            s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
            filter_values = [tenant, s_cloud_name]
            m_tenants = tenants.get_migrated_tenant(filter_values)
            migrated_tenant = m_tenants[0] if m_tenants else None
            if not migrated_tenant:
                print ("The tenant to which the image belongs to hasn't" +
                       "been migrated yet.")
                return
            if migrated_tenant.images_migrated:
                # images already migrated for this tenant
                print ("All images have been migrated for tenant '%s'"
                       % migrated_tenant.project_name)
                return

            images_to_migrate = self.gl_source.list(
                owner=migrated_tenant.src_uuid)

            for image in images_to_migrate:
                self.migrate_one_image(image)