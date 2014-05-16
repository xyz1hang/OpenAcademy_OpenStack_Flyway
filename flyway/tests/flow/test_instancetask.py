import time
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

        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

        self.gl_source = get_glance_source()
        self.gl_target = get_glance_target()

        self.nv_source = get_nova_source()
        self.nv_target = get_nova_target()

        # create a tenant on the source cloud for instance migration
        self.tenant_name = 'tenant_tenant'
        self.image_name = 'cirros-0.3.1-x86_64-uec-kernel'
        self.tenant_source = self.ks_source.tenants.create(self.tenant_name,
                                                           "", True)
        self.nv_source_tenant = get_nova_source(self.tenant_name)

        user = self.ks_source.users.find(name="admin")
        role = self.ks_source.roles.find(name="admin")

        self.ks_source.roles.add_user_role(user=user,
                                           role=role,
                                           tenant=self.tenant_source)

    def test_migrate_instance(self):
        server_name = "instance_name"
        vm_migrated = None

        images = self.gl_source.images.list()
        for one_image in images:
            if one_image.name.find(self.image_name) > -1:
                print one_image.name
                image = self.nv_source.images.find(name=one_image.name)
                self.image_source = image
                flavor = self.nv_source.flavors.find(name="m1.micro")
                vm_migrated = self.nv_source_tenant.servers.create(name=server_name, image=image, flavor=flavor)

        status = vm_migrated.status
        while status == 'BUILD':
            time.sleep(5)
            instance = self.nv_source.servers.get(vm_migrated.id)
            if instance.status == 'ERROR' or 'ACTIVE':
                break
            print instance.status
        # migrate tenant, flavor, image and key pair at first
        values = {'users_to_move': [],
                  'tenants_to_move': [self.tenant_name],
                  'flavors_to_migrate': ['m1.micro'],
                  'images_to_migrate': [self.image_source.id],
                  'tenant_to_process': [],
                  'keypairs_to_move': [],
                  'roles_to_migrate': [],
                  'tenant_vm_dicts': {self.tenant_name: [vm_migrated.id]}}

        server_target = None
        flavor_target = None
        key_target = None
        image_target = None
        tenant_target = None
        try:
            flow.execute(values)

            self.nv_target_tenant = get_nova_target(self.tenant_name)

            server_target = self.nv_target_tenant.servers.\
                find(name=server_name)
            self.assertIsNot(None, server_target)

            tenant_target = self.ks_target.tenants.find(name=self.tenant_name)

        except Exception, e:
            self.fail(e)

        finally:
            values = [server_name,
                      vm_migrated.id,
                      cfg.CONF.SOURCE.os_cloud_name,
                      cfg.CONF.TARGET.os_cloud_name]
            instances.delete_migration_record(values)

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
            #self.nv_source.flavors.delete(self.flavor_source)
            #self.nv_source.keypairs.delete(self.key_source)
            #self.gl_source.images.delete(self.image_source)
            self.ks_source.tenants.delete(self.tenant_source)

            if server_target:
                self.nv_target_tenant.servers.delete(server_target)

            if image_target:
                self.gl_target.images.delete(image_target)

            if tenant_target:
                self.ks_target.tenants.delete(tenant_target)
