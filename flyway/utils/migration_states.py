__author__ = 'hydezhang'
from enum import Enum


class MigrationState(Enum):
    completed = 'Completed'
    error = 'Error'
    skipped = 'Skipped'
    default = 'Unknown'


class InstanceMigrationState(MigrationState):
    launching_proxy = 'launching_proxy'

    proxy_launched = 'proxy_launched'
    proxy_launching_failed = 'proxy_launching_failed'

    dst_instance_stopped = 'destination_instance_stopped'
    stop_instance_failed = 'stop_instance_failed'

    source_instance_missing = 'source_instance_missing'
    proxy_instance_missing = 'proxy_instance_missing'

    disk_file_migrate_failed = 'disk_file_migrate_failed'
    disk_file_migrated = 'disk_file_migrated'

    instance_booting_failed = 'instance_booting_failed'

