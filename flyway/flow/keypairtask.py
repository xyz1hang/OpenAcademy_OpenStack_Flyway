import logging
from taskflow import task
import utils.helper
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
        self.nv_source = utils.helper.get_nova_source()
        self.nv_target = utils.helper.get_nova_target()

        self.s_cloud_name = utils.helper.cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = utils.helper.cfg.CONF.TARGET.os_cloud_name

    def migrate_one_keypair(self, keypair_name):
        try:
            s_keypair = self.nv_source.keypairs.find(name=keypair_name)
        except nova_exceptions.NotFound:
            # encapsulate exceptions to make it more understandable
            # to user. Other exception handling mechanism can be added later
            raise exceptions.ResourceNotFoundException(
                ResourceType.keypair, keypair_name,
                utils.helper.cfg.CONF.SOURCE.os_cloud_name)

        # create a new keypair
        values = [s_keypair.name, self.s_cloud_name, self.t_cloud_name]
        keypair_data = db_handler.get_migrated_keypairs(values)
        migrated_keypair = None
        try:
            migrated_keypair = self.nv_target.keypairs.create(s_keypair.name,
                                                              public_key=s_keypair.public_key)
        except IOError as (err_no, strerror):
            print "I/O error({0}): {1}".format(err_no, strerror)
        except:
            # TODO: not sure what exactly the exception will be thrown
            # TODO: upon creation failure
            print "tenant {} migration failure".format(s_keypair.name)
            # update database record
            keypair_data = keypair_data.update({'state': "error"})
            db_handler.update_keypairs(**keypair_data)
            return

        keypair_data.update({'dst_uuid': migrated_keypair.id})
        keypair_data.update({'state': 'completed'})
        db_handler.update_keypairs(**keypair_data)

    def execute(self, keypairs_to_move=[]):
        """execute the keypair migration task

        :param keypairs_to_move: the list of keypairs to move. If the not specified
        or length equals to 0 all tenant will be migrated, otherwise only
        specified keypairs will be migrated
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
                keypairs_to_move.append(keypair.name)
        else:
            LOG.info("Migrating given keypairs of size {} ...\n"
                     .format(len(keypairs_to_move)))

        for keypair_name in keypairs_to_move:
            values = [keypair_name, self.s_cloud_name, self.t_cloud_name]
            m_keypair = db_handler.get_migrated_keypairs(values)

            # add keypairs that have not been stored in the database
            if m_keypair is None:
                # check for keypair name duplication
                new_name = keypair_name
                try:
                    found = self.nv_target.keypairs.find(name=keypair_name)
                    if found:
                        user_input = \
                            raw_input("duplicated keypair {0} found on " +
                                      "cloud {1}\nPlease type in a new name or " +
                                      "'abort':".format(found.name, self.t_cloud_name))
                        if user_input is "abort":
                            # TODO: implement cleaning up and proper exit
                            return None
                        elif user_input:
                            new_name = user_input
                except nova_exceptions.NotFound:
                    # irrelevant exception - swallow
                    pass

                try:
                    keypair = self.nv_source.keypairs.find(name=keypair_name)
                except nova_exceptions.NotFound:
                    # encapsulate exceptions to make it more understandable
                    # to user. Other exception handling mechanism can be added later
                    raise exceptions.ResourceNotFoundException(
                        ResourceType.keypair, keypair_name,
                        utils.helper.cfg.CONF.SOURCE.os_cloud_name)

                keypair_data = {'name': keypair.name,
                                'public_key': keypair.public_key,
                                'src_uuid': keypair.id,
                                'src_cloud': self.s_cloud_name,
                                'new_name': new_name,
                                'dst_uuid': keypair.id,
                                'dst_cloud': self.t_cloud_name,
                                'state': "unknown"}
                db_handler.record_keypair_migrated([keypair_data])

                LOG.info("Migrating keypair '{}'\n".format(keypair_name))
                self.migrate_one_keypair(keypair_name)

            else:
                if m_keypair['state'] is "completed":
                    print("keypair {0} in cloud {1} has already been migrated"
                          .format(keypair_name, self.s_cloud_name))
                else:
                    LOG.info("Migrating keypair '{}'\n".format(keypair_name))
                    self.migrate_one_keypair(keypair_name)