import logging
import sys

sys.path.append('../')

from taskflow import task
from utils.helper import *
from utils.db_base import *
import time

LOG = logging.getLogger(__name__)


class KeypairMigrationTask(task.Task):
    """Task to migrate all keypairs from the source cloud to the target cloud.
        """

    def __init__(self, *args, **kwargs):
        super(KeypairMigrationTask, self).__init__(**kwargs)

        self.nv_source = get_nova_source()
        self.nv_target = get_nova_target()

        self.target_keypair_public_keys = []
        for keypair in self.nv_target.keypairs.list():
            self.target_keypair_public_keys.append(keypair.public_key)

        self.initialise_db()

    def migrate_one_keypair(self, keypair):
        if keypair.public_key not in self.target_keypair_public_keys:
            self.nv_target.keypairs.create(keypair.name,
                                           public_key=keypair.public_key)
            set_dict = {'completed': 'YES'}
            where_dict = {'name': keypair.name}
            start = time.time()
            while True:
                if time.time() - start > 3:
                    print 'Fail!!!'
                    break
                elif self.migration_succeed(keypair):
                    update_table('keypairs', set_dict, where_dict, False)
                    break

    def migration_succeed(self, keypair):
        for target_keypair in self.nv_target.keypairs.list():
            if keypair.public_key == target_keypair.public_key:
                return True

        return False

    def initialise_db(self):

        table_columns = '''id INT NOT NULL AUTO_INCREMENT,
                                   name VARCHAR(64) NOT NULL,
                                   public_key LONGTEXT NOT NULL,
                                   completed VARCHAR(10) NOT NULL,
                                   PRIMARY KEY(id),
                                   UNIQUE (name)
                                '''

        if not check_table_exist('keypairs'):
            create_table('keypairs', table_columns, False)

        values = []
        for keypair in self.nv_source.keypairs.list():
            if keypair.public_key not in self.target_keypair_public_keys:
                values.append("null, '{0}', '{1}', 'NO'"
                              .format(keypair.name, keypair.public_key))

        insert_record('keypairs', values, False)

    def execute(self):
        LOG.info('Migrating all keypairs ...')

        for keypair in self.nv_source.keypairs.list():
            self.migrate_one_keypair(keypair)