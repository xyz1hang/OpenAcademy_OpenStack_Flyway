from utils.db_base import delete_all_data

__author__ = 'chengxue'

from tests.flow.test_base import TestBase
from flyway.flow import flow
from flyway.utils.helper import *
from keystoneclient import exceptions as ks_exceptions
from utils.db_handlers import tenants
from utils.db_handlers import users
from utils.db_handlers import flavors
from utils.db_handlers import keypairs
from utils.db_handlers import images


class SpecifyResourceTest(TestBase):
    def __init__(self, *args, **kwargs):
        super(SpecifyResourceTest, self).__init__(*args, **kwargs)

        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()
        self.nv_source = get_nova_source()
        self.nv_target = get_nova_target()
        self.gl_source = get_glance_source()
        self.gl_target = get_glance_target()
        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name
        self.reset_value()

    def reset_value(self):
        self.value = {'tenants_to_move': [],
                      'flavors_to_migrate': [],
                      'images_to_migrate': [],
                      'tenant_to_process': [],
                      'keypairs_to_move': [],
                      'roles_to_migrate': [],
                      'tenant_vm_dicts': {},
                      'name_of_roles_to_move': [],
                      'users_to_move': []}

    def test_user_migration(self):
        user_name = "tester"
        user_to_migrate = self.ks_source.users.create(
            user_name, password="password")

        self.reset_value()
        self.value['users_to_move'].append(user_name)
        flow.execute(self.value)

        user_target = None
        values_u = [user_name, self.s_cloud_name, self.t_cloud_name]
        try:
            user_target = self.ks_target.users.find(name=user_name)

            self.assertIsNotNone(user_target)

            all_users = self.ks_target.users.list()
            self.assertIn(user_target, all_users)

            user_data = users.get_migrated_user(values_u)

            self.assertEqual("completed", user_data['state'])

        except ks_exceptions.NotFound, e:
            self.fail(e)
        finally:
            self.ks_source.users.delete(user_to_migrate)
            if user_target is not None:
                self.ks_target.users.delete(user_target)
            users.delete_migrated_users()

    def test_role_migration(self):
        role_name = "tester"
        role_to_migrate = self.ks_source.roles.create(role_name)

        self.reset_value()
        self.value['roles_to_migrate'].append(role_name)
        flow.execute(self.value)

        role_target = None
        try:
            role_target = self.ks_target.roles.find(name=role_name)

            self.assertIsNotNone(role_target)

            all_roles = self.ks_target.roles.list()
            self.assertIn(role_target, all_roles)

        except ks_exceptions.NotFound, e:
            self.fail(e)
        finally:
            self.ks_source.roles.delete(role_to_migrate)
            if role_target is not None:
                self.ks_target.roles.delete(role_target)
            delete_all_data('roles')

    def test_tenant_migration(self):
        tenant_name = "tenant_test"
        tenant_to_migrate = self.ks_source.tenants.create(
            tenant_name, "for testing", True)

        self.reset_value()
        self.value['tenants_to_move'].append(tenant_name)
        flow.execute(self.value)

        tenant_target = None
        values_t = [tenant_name, self.s_cloud_name, self.t_cloud_name]
        try:
            tenant_target = self.ks_target.tenants.find(name=tenant_name)

            self.assertIsNotNone(tenant_target)

            tenant_data = tenants.get_migrated_tenant(values_t)

            self.assertEqual("proxy_created", tenant_data['state'])

        except ks_exceptions.NotFound, e:
            self.fail(e)
        finally:
            self.ks_source.tenants.delete(tenant_to_migrate)
            if tenant_target is not None:
                self.ks_target.tenants.delete(tenant_target)
            values_t = [tenant_name, tenant_to_migrate.id,
                        self.s_cloud_name, self.t_cloud_name]
            tenants.delete_migration_record(values_t)

    def test_flavor_migration(self):
        flavor_name = 'flavor_test'
        test_flavor_details = {'name': flavor_name,
                               'ram': 512,
                               'vcpus': 1,
                               'disk': 1,
                               'ephemeral': 0,
                               'swap': 0,
                               'rxtx_factor': 1.0,
                               'is_public': 'True'}

        flavor_to_migrate = self.\
            nv_source.flavors.create(**test_flavor_details)
        self.reset_value()
        self.value['flavors_to_migrate'].append(flavor_name)
        flow.execute(self.value)
        migrated_flavor = None
        try:

            migrated_flavor = self.nv_target.flavors.find(
                name=flavor_name)

            self.assertEqual(flavor_to_migrate.name, migrated_flavor.name)

        except Exception as e:
            self.fail(e)
        finally:
            self.nv_source.flavors.delete(flavor_to_migrate)
            filter_values = [flavor_to_migrate.name, flavor_to_migrate.id,
                             cfg.CONF.SOURCE.os_cloud_name,
                             cfg.CONF.TARGET.os_cloud_name]
            flavors.delete_migration_record(filter_values)

            if migrated_flavor:
                self.nv_target.flavors.delete(migrated_flavor)

    def test_keypair_migration(self):
        keypair_name = 'keypair_test'

        keypair_to_migrate = self.\
            nv_source.keypairs.create(name=keypair_name)
        keypair_fingerprint = keypair_to_migrate.fingerprint
        self.reset_value()
        self.value['keypairs_to_move'].append(keypair_fingerprint)
        flow.execute(self.value)
        migrated_keypair = None
        try:

            migrated_keypair = self.nv_target.keypairs.find(
                fingerprint=keypair_fingerprint)

            self.assertEqual(keypair_to_migrate.name, migrated_keypair.name)

        except Exception as e:
            self.fail(e)
        finally:
            self.nv_source.keypairs.delete(keypair_to_migrate)
            filter_values = [keypair_to_migrate.fingerprint,
                             cfg.CONF.SOURCE.os_cloud_name,
                             cfg.CONF.TARGET.os_cloud_name]
            keypairs.delete_keypairs(filter_values)

            if migrated_keypair:
                self.nv_target.keypairs.delete(migrated_keypair)

    def test_image_migration(self):
        image_name = 'image_test'
        image_to_migrate = self.gl_source.images.create(
            name=image_name,
            disk_format='qcow2',
            container_format='bare',
            is_public=True,
            location='http://cloud-images.ubuntu.com/releases/12.04.2/release/'
                     'ubuntu-12.04-server-cloudimg-amd64-disk1.img')
        self.reset_value()
        self.value['images_to_migrate'].append(image_to_migrate.id)
        flow.execute(self.value)
        migrated_image = None
        try:
            filters = {"src_image_name": image_name,
                       "src_uuid": image_to_migrate.id,
                       "src_cloud": self.s_cloud_name,
                       "dst_cloud": self.t_cloud_name}
            image_migration_record = images.get_migrated_image(filters)
            dest_id = image_migration_record[0]['dst_uuid']
            dest_image = self.gl_target.images.get(dest_id)

            self.assertEqual(image_to_migrate.name, dest_image.name)
            self.assertEqual(image_to_migrate.disk_format,
                             dest_image.disk_format)
            self.assertEqual(image_to_migrate.container_format,
                             dest_image.container_format)
            self.assertEqual(image_to_migrate.is_public,
                             dest_image.is_public)

        except Exception, e:
            self.fail(e)
        finally:
            self.gl_source.images.delete(image_to_migrate)
            # clean database
            filter_values = [image_to_migrate.name,
                             image_to_migrate.id,
                             image_to_migrate.owner,
                             self.s_cloud_name,
                             self.t_cloud_name]
            images.delete_migration_record(filter_values)

            if migrated_image:
                self.gl_target.images.delete(migrated_image)
