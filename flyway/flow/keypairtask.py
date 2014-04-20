import logging
from taskflow import task
from utils.helper import *
from utils.resourcetype import ResourceType
from utils.db_handlers import keypairs as db_handler
from utils import exceptions
from novaclient import exceptions as nova_exceptions

LOG = logging.getLogger(__name__)


class KeypairMigrationTask(task.Task):
    """
    Task to migrate all keypairs from the source cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(KeypairMigrationTask, self).__init__(*args, **kwargs)
        # config must be ready at this point
        self.nv_source = get_nova_source()
        self.nv_target = get_nova_target()

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        self.s_user_name = cfg.CONF.SOURCE.os_username

    def migrate_one_keypair(self, keypair_fingerprint):
        # create a new keypair
        values = [keypair_fingerprint, self.s_cloud_name, self.t_cloud_name]
        keypair_data = db_handler.get_keypairs(values)
        migrated_keypair = None
        try:
            migrated_keypair = self.nv_target.keypairs.create(
                keypair_data['name'], public_key=keypair_data['public_key'])
            user_id = migrated_keypair.user_id
        except IOError as (err_no, strerror):
            print "I/O error({0}): {1}".format(err_no, strerror)
        except:
            # TODO: not sure what exactly the exception will be thrown
            # TODO: upon creation failure
            print "Keypair {} migration failure".format(keypair_data['name'])
            # update database record
            keypair_data = keypair_data.update({'state': "error"})
            db_handler.update_keypairs(**keypair_data)
            return

        keypair_data.update({'state': 'completed'})
        db_handler.update_keypairs(**keypair_data)

    def execute(self, keypairs_to_move=None):
        """execute the keypair migration task

        :param keypairs_to_move: the list of keypairs to move.
        If the not specified or length equals to 0 all keypair will be
        migrated, otherwise only specified keypairs will be migrated
        """

        # in case only one string gets passed in
        if type(keypairs_to_move) is str:
            keypairs_to_move = [keypairs_to_move]

        # create new table if not exists
        db_handler.initialise_keypairs_mapping()

        if not keypairs_to_move or len(keypairs_to_move) == 0:
            LOG.info("Migrating all keypairs ...")
            keypairs_to_move = []
            for keypair in self.nv_source.keypairs.list():
                keypairs_to_move.append(keypair.fingerprint)
        else:
            LOG.info("Migrating given keypairs of size {} ...\n"
                     .format(len(keypairs_to_move)))

        for keypair_fingerprint in keypairs_to_move:
            values = [keypair_fingerprint, self.s_cloud_name,
                      self.t_cloud_name]
            m_keypair = db_handler.get_keypairs(values)

            # add keypairs that have not been stored in the database
            if m_keypair is None:
                try:
                    s_keypair = self.nv_source.keypairs.\
                        find(fingerprint=keypair_fingerprint)
                except nova_exceptions.NotFound:
                    # encapsulate exceptions to make it more understandable
                    # to user. Other exception handling
                    # mechanism can be added later
                    raise exceptions.ResourceNotFoundException(
                        ResourceType.keypair, keypair_fingerprint,
                        cfg.CONF.SOURCE.os_cloud_name)

                keypair_data = {'name': s_keypair.name,
                                'public_key': s_keypair.public_key,
                                'fingerprint': s_keypair.fingerprint,
                                'user_name': self.s_user_name,
                                'src_cloud': self.s_cloud_name,
                                'dst_cloud': self.t_cloud_name,
                                'state': "unknown",
                                'user_id_updated': "0"}
                db_handler.record_keypairs([keypair_data])

                LOG.info("Migrating keypair '{}'\n".format(s_keypair.name))
                self.migrate_one_keypair(keypair_fingerprint)

            else:
                if m_keypair['state'] == "completed":
                    print("keypair {0} in cloud {1} has already been migrated"
                          .format(m_keypair['name'], self.s_cloud_name))
                else:
                    LOG.info("Migrating keypair '{}'\n".
                             format(m_keypair['name']))
                    self.migrate_one_keypair(keypair_fingerprint)