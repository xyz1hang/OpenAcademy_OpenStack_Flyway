__author__ = 'hydezhang'

from keystoneclient import exceptions as keystone_exceptions
from oslo.config import cfg

from tests.flow.test_base import TestBase
from flow.flavortask import FlavorMigrationTask
from common import config
from utils.db_handlers import flavors


class FlavorTaskTest(TestBase):
    """Unit test for Flavor migration"""

    def __init__(self, *args, **kwargs):
        super(FlavorTaskTest, self).__init__(*args, **kwargs)
        config.parse(['--config-file', '../../etc/flyway.conf'])
        self.migration_task = FlavorMigrationTask('flavor_migration_task')

    def test_execute(self):
        test_flavor_name = 'Flavor_on_source'
        test_flavor_details = {'name': test_flavor_name,
                               'ram': 512,
                               'vcpus': 1,
                               'disk': 1,
                               'ephemeral': 0,
                               'swap': 0,
                               'rxtx_factor': 1.0,
                               'is_public': 'True'}

        flavor_to_migrate = self.migration_task. \
            nv_source.flavors.create(**test_flavor_details)

        migrated_flavor = None
        try:
            self.migration_task.execute([test_flavor_name])

            migrated_flavor = self.migration_task.nv_target.flavors.find(
                name=test_flavor_name)

            self.assertEqual(flavor_to_migrate.name, migrated_flavor.name)

        except keystone_exceptions.NotFound as e:
            print str(e)
        finally:
            self.clean_up(flavor_to_migrate, migrated_flavor)

    def clean_up(self, flavor_to_migrate, migrated_flavor=None):
        self.migration_task.nv_source.flavors.delete(flavor_to_migrate)
        # clean database
        filter_values = [flavor_to_migrate.name, flavor_to_migrate.id,
                         cfg.CONF.SOURCE.os_cloud_name,
                         cfg.CONF.TARGET.os_cloud_name]
        flavors.delete_migration_record(filter_values)

        if migrated_flavor:
            self.migration_task.nv_target.flavors.delete(migrated_flavor)