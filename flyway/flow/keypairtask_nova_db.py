import logging
from taskflow import task
from utils.helper import *
from utils.db_handlers import keypairs as db_handler
from utils.db_base import *

LOG = logging.getLogger(__name__)


class KeypairNovaDBMigrationTask(task.Task):
    """
    Task to migrate all keypairs from the source cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(KeypairNovaDBMigrationTask, self).__init__(*args, **kwargs)
        # config must be ready at this point
        self.nv_target = get_nova_target()

        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name

    def migrate_one_keypair(self, keypair_fingerprint):
        # create a new keypair
        values = [keypair_fingerprint, self.s_cloud_name, self.t_cloud_name]
        keypair_data = db_handler.get_keypairs(values)
        migrated_keypair = None
        try:
            migrated_keypair = self.nv_target.keypairs.create(
                keypair_data['name'], public_key=keypair_data['public_key'])
        except IOError as (err_no, strerror):
            print "I/O error({0}): {1}".format(err_no, strerror)
        except:
            # TODO: not sure what exactly the exception will be thrown
            # TODO: upon creation failure
            print "tenant {} migration failure".format(keypair_data['name'])
            # update database record
            keypair_data = keypair_data.update({'state': "error"})
            db_handler.update_keypairs(**keypair_data)
            return

        # get the corresponding user_id (in targer) of the
        # keypair using the user_name, which should be the
        # same as the source
        user_id = db_handler.\
            get_info_from_openstack_db(host='192.168.50.5',
                                       db_name='keystone',
                                       table_name='user',
                                       columns=['id'],
                                       filters={"name":
                                                keypair_data['user_name']})

        # because the default user to create the keypair is 'admin',
        # need to update the user_id (in target) of the keypair
        db_handler.\
            update_info_on_openstack_db(host='192.168.50.5',
                                        db_name='nova',
                                        table_name='key_pairs',
                                        set_id={"user_id": user_id[0][0]},
                                        filters={"fingerprint":
                                                 keypair_fingerprint,
                                                 "deleted": '0'})

        keypair_data.update({'state': 'completed'})
        db_handler.update_keypairs(**keypair_data)

    def execute(self, keypairs_to_move=None):
        # in case only one string gets passed in
        if type(keypairs_to_move) is str:
            keypairs_to_move = [keypairs_to_move]

        # create new table if not exists
        db_handler.initialise_keypairs_mapping()

        if not keypairs_to_move or len(keypairs_to_move) == 0:
            LOG.info("Migrating all keypairs ...")
            keypairs_to_move = []

            # get all keypairs from the table 'key_pairs' in 'nova'
            fingerprints = db_handler.\
                get_info_from_openstack_db(table_name="key_pairs",
                                           db_name='nova',
                                           host='192.168.50.4',
                                           columns=['fingerprint'],
                                           filters={"deleted": '0'})
            for one_fingerprint in fingerprints:
                keypairs_to_move.append(one_fingerprint[0])

        else:
            LOG.info("Migrating given keypairs of size {} ...\n"
                     .format(len(keypairs_to_move)))

        for keypair_fingerprint in keypairs_to_move:
            values = [keypair_fingerprint, self.s_cloud_name,
                      self.t_cloud_name]
            m_keypair = db_handler.get_keypairs(values)

            # add keypairs that have not been stored in the database
            if m_keypair is None:
                # get keypair information from nova using fingerprint
                result = db_handler.\
                    get_info_from_openstack_db(table_name="key_pairs",
                                               db_name='nova',
                                               host='192.168.50.4',
                                               columns=['*'],
                                               filters={"fingerprint":
                                                        keypair_fingerprint})
                # get the corresponding user_name (in source)
                # of the keypair using user_id
                user_name = db_handler.\
                    get_info_from_openstack_db(table_name="user",
                                               db_name='keystone',
                                               host='192.168.50.4',
                                               columns=['name'],
                                               filters={"id": result[0][5]})

                keypair_data = {'name': result[0][4],
                                'public_key': result[0][7],
                                'fingerprint': result[0][6],
                                'user_name': user_name[0][0],
                                'src_cloud': self.s_cloud_name,
                                'dst_cloud': self.t_cloud_name,
                                'state': "unknown"}
                db_handler.record_keypairs([keypair_data])

                LOG.info("Migrating keypair '{}'\n".format(result[0][4]))
                self.migrate_one_keypair(keypair_fingerprint)

            else:
                if m_keypair['state'] == "completed":
                    print("keypair {0} in cloud {1} has already been migrated"
                          .format(m_keypair['name'], self.s_cloud_name))
                else:
                    LOG.info("Migrating keypair '{}'\n".
                             format(m_keypair['name']))
                    self.migrate_one_keypair(keypair_fingerprint)