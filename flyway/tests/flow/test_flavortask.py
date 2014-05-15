from utils.db_base import read_record

__author__ = 'hydezhang'

from keystoneclient import exceptions as keystone_exceptions
from oslo.config import cfg

from tests.flow.test_base import TestBase
from flow.flavortask import FlavorMigrationTask
from utils.db_handlers import flavors


class FlavorTaskTest(TestBase):
    """Unit test for Flavor migration"""

    def __init__(self, *args, **kwargs):
        super(FlavorTaskTest, self).__init__(*args, **kwargs)
        self.migration_task = FlavorMigrationTask('flavor_migration_task')

    def test_execute(self):
        self.migration_task.execute([])
        self.migration_task.execute(None)

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

            # try to migrate one flavor that has been existed on the target
            self.migration_task.execute([test_flavor_name])

            # try to migrate one flavor that is not in the source cloud
            self.migration_task.execute(["flavor_not_on_source"])

        except keystone_exceptions.NotFound as e:
            self.fail(e)
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

    def test_revert(self):
        self.migration_task.revert([])
        self.migration_task.revert(None)

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
            self.migration_task.revert([test_flavor_name])

            data = read_record("flavors", ['*'], {"name": "test_flavor_name"}, True)
            self.assertEqual(None, data)

        except keystone_exceptions.NotFound:
            pass
        finally:
            self.clean_up(flavor_to_migrate, migrated_flavor)