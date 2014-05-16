from flow import flow

__author__ = 'chengxue'

from tests.flow.test_base import TestBase
from flow.instancetask import InstanceMigrationTask
from flow.imagetask import ImageMigrationTask
from flow.keypairtask import KeypairMigrationTask
from flow.flavortask import FlavorMigrationTask
from flow.tenanttask import TenantMigrationTask
from utils.db_handlers import instances
from utils.db_handlers import images
from utils.db_handlers import flavors
from utils.db_handlers import keypairs
from utils.db_handlers import tenants
from utils.helper import *
from oslo.config import cfg


class InstanceTaskTest(TestBase):
    """Unit test for Instance migration"""

    def __init__(self, *args, **kwargs):
        super(InstanceTaskTest, self).__init__(*args, **kwargs)
        self.migration_task = InstanceMigrationTask('instance_migration_task')
        self.image_task = ImageMigrationTask('image_migration_task')
        self.tenant_task = TenantMigrationTask('tenant_migration_task')
        self.flavor_task = FlavorMigrationTask('flavor_migration_task')
        self.keypair_task = KeypairMigrationTask('keypair_migration_task')

        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.gl_source = get_glance_source()
        self.gl_target = get_glance_target()

        self.nv_source = get_nova_source()
        self.nv_target = get_nova_target()

        # create an image on the source cloud for instance migration
        self.image_name = "image"
        self.image_source = self.gl_source.images.create(
            name=self.image_name,
            disk_format='qcow2',
            container_format='bare',
            is_public=True,
            location='http://cloud-images.ubuntu.com/releases/12.04.2/release/'
                     'ubuntu-12.04-server-cloudimg-amd64-disk1.img')

        # create a flavor on the source cloud for instance migration
        self.flavor_name = 'flavor'
        self.flavor_data = {'name': self.flavor_name,
                       'ram': 512,
                       'vcpus': 1,
                       'disk': 1,
                       'ephemeral': 0,
                       'swap': 0,
                       'rxtx_factor': 1.0,
                       'is_public': 'True'}
        self.flavor_source = self.nv_source.flavors.create(**self.flavor_data)

        # create a key pair on the source cloud for instance migration
        self.key_name = 'key pair'
        self.key_source = self.nv_source.keypairs.create(name=self.key_name)

        # create a tenant on the source cloud for instance migration
        self.tenant_name = 'tenant_tenant'
        self.tenant_source = self.ks_source.tenants.create(self.tenant_name,
                                                           "", True)

        self.nv_source_tenant = get_nova_source(self.tenant_name)
        self.nv_target_tenant = get_nova_target(self.tenant_name)

        user = self.ks_source.users.find(name="admin")
        role = self.ks_source.roles.find(name="admin")

        self.ks_source.roles.add_user_role(user=user,
                                           role=role,
                                           tenant=self.tenant_source)

    def test_migrate_tenant(self):
        server_name = "instance_name"
        vm_migrated = self.nv_source_tenant.servers.create(name=server_name,
                                                    image=self.image_source,
                                                    flavor=self.flavor_source,
                                                    keypairs=self.key_source)

        # migrate tenant, flavor, image and key pair at first
        values = {'users_to_move': [],
                  'tenants_to_move': [self.tenant_name],
                  'flavors_to_migrate': [self.flavor_name],
                  'images_to_migrate': [self.image_source.id],
                  'tenant_to_process': [],
                  'keypairs_to_move': [self.key_source.fingerprint],
                  'roles_to_migrate': [],
                  'tenant_vm_dicts': {self.tenant_name: [vm_migrated.id]}}

        server_target = None
        flavor_target = None
        key_target = None
        image_target = None
        tenant_target = None
        try:
            flow.execute(values)

            server_target = self.nv_target_tenant.servers.\
                find(name=server_name)
            self.assertIsNot(None, server_target)

            flavor_target = self.nv_target.flavors.find(name=self.flavor_name)
            key_target = self.nv_target.keypairs.find(name=self.key_name)
            image_target = self.gl_target.images.find(name=self.image_name)
            tenant_target = self.ks_target.tenants.find(name=self.tenant_name)

        except:
            self.fail()

        finally:
            values = [server_name,
                      vm_migrated.id,
                      cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            instances.delete_migration_record(values)

            values = [self.flavor_name,
                      self.flavor_source.id,
                      cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            flavors.delete_migration_record(values)

            values = [self.key_source.fingerprint,
                      cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            keypairs.delete_keypairs(values)

            values = [self.tenant_name,
                      self.tenant_source.id,
                      cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            tenants.delete_migration_record(values)

            values = [self.image_name,
                      self.image_source.id,
                      self.tenant_source.id,
                      cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            images.delete_migration_record(values)

            self.nv_source_tenant.servers.delete(vm_migrated)
            self.nv_source.flavors.delete(self.flavor_source)
            self.nv_source.keypairs.delete(self.key_source)
            self.gl_source.images.delete(self.image_source)
            self.ks_source.tenants.delete(self.tenant_source)

            if server_target:
                self.nv_target_tenant.servers.delete(server_target)
            if flavor_target:
                self.nv_target.flavors.delete(flavor_target)
            if key_target:
                self.nv_target.keypairs.delete(key_target)
            if image_target:
                self.gl_target.images.delete(image_target)
            if tenant_target:
                self.ks_target.tenants.delete(tenant_target)