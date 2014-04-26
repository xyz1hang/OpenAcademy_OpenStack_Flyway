from tests.flow.test_base import TestBase

__author__ = 'chengxue'

from novaclient import exceptions as nova_exceptions
from flyway.common import config
from flyway.flow.keypairtask import KeypairMigrationTask
from flyway.flow.update_keypair_user_task import UpdateKeypairUserTask
from utils.db_handlers import keypairs
from utils.helper import *


class KeypairTaskTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(KeypairTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = \
            KeypairMigrationTask('keypair_migration_task')
        self.update_task = UpdateKeypairUserTask('keypair_user_task')

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name
        self.nv_source = get_nova_source()
        self.nv_target = get_nova_target()

    def test_execute(self):
        keypair_name = "keypair_update_test"
        keypair_to_migrate = self.nv_source.keypairs.create(
            keypair_name)

        keypair_fingerprint = keypair_to_migrate.fingerprint
        self.migration_task.execute([keypair_fingerprint])
        self.update_task.execute()

        migrated_keypair = None
        try:
            # get the tenant data that has been migrated from src to dst
            values = [keypair_fingerprint, self.s_cloud_name,
                      self.t_cloud_name]
            keypair_data = keypairs.get_keypairs(values)

            migrated_keypair = self.nv_target.keypairs.\
                find(fingerprint=keypair_fingerprint)

            self.assertIsNotNone(migrated_keypair)
            self.assertEqual("completed", keypair_data['state'])
            self.assertEqual(1, keypair_data['user_id_updated'])
            self.assertEqual(keypair_data["new_name"], migrated_keypair.name)

        except nova_exceptions.NotFound:
            self.nv_source.tenants.delete(keypair_to_migrate)
            return

        finally:
            self.nv_source.keypairs.delete(keypair_to_migrate)
            if migrated_keypair is not None:
                self.nv_target.keypairs.delete(migrated_keypair)
            values = [keypair_fingerprint, self.s_cloud_name,
                      self.t_cloud_name]
            keypairs.delete_keypairs(values)