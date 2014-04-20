from tests.flow.test_base import TestBase

__author__ = 'chengxue'

from novaclient import exceptions as nova_exceptions
from flyway.common import config
from flyway.flow.keypairtask import KeypairMigrationTask
from utils.db_handlers import keypairs as db_handler
import utils.helper


class KeypairTaskTest(TestBase):

    def __init__(self, *args, **kwargs):
        super(KeypairTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = KeypairMigrationTask('keypair_migration_task')

        self.s_cloud_name = utils.helper.cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = utils.helper.cfg.CONF.TARGET.os_cloud_name

    def test_execute(self):
        keypair_name = "keypair_name_test"
        keypair_to_migrate = self.migration_task.nv_source.keypairs.create(
            keypair_name)

        keypair_fingerprint = keypair_to_migrate.fingerprint
        self.migration_task.execute([keypair_fingerprint])

        migrated_keypair = None
        try:
            # get the tenant data that has been migrated from src to dst
            values = [keypair_fingerprint, self.s_cloud_name,
                      self.t_cloud_name]
            keypair_data = db_handler.get_keypairs(values)

            migrated_keypair = self.migration_task.nv_target.keypairs.\
                find(fingerprint=keypair_fingerprint)

            self.assertIsNotNone(migrated_keypair)
            self.assertEqual("completed", keypair_data['state'])

        except nova_exceptions.NotFound:
            self.migration_task.nv_source.tenants.delete(keypair_to_migrate)
            return

        finally:
            self.migration_task.nv_source.keypairs.delete(keypair_to_migrate)
            if migrated_keypair is not None:
                self.migration_task.nv_target.keypairs.\
                    delete(migrated_keypair)
            values = [keypair_fingerprint, self.s_cloud_name,
                      self.t_cloud_name]
            db_handler.delete_keypairs(values)