__author__ = 'chengxue'

import unittest
from flyway.common import config
from flyway.flow.keypairtask import KeypairMigrationTask
from novaclient import exceptions as nova_exceptions
from utils.db_handlers import keypairs as db_handler
import utils.helper


class KeypairTaskTest(unittest.TestCase):

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

        self.migration_task.execute(keypair_name)

        try:
            migrated_keypair = self.migration_task.nv_target.keypairs.find(
                name=keypair_name)

            self.assertEqual(keypair_to_migrate.name, migrated_keypair.name)

        except nova_exceptions.NotFound:
            self.migration_task.ks_source.tenants.delete(keypair_to_migrate)
            return

        finally:
            self.migration_task.nv_source.keypairs.delete(keypair_to_migrate)
            self.migration_task.nv_target.keypairs.delete(migrated_keypair)

            values = [keypair_name, self.s_cloud_name, self.t_cloud_name]
            db_handler.delete_keypairs(values)