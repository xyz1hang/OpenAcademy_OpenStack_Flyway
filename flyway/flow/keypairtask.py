import logging
from taskflow import task
from utils.helper import *
from utils.db_handlers import keypairs as db_handler
from utils.db_base import *
from time import localtime, time, strftime


LOG = logging.getLogger(__name__)


class KeypairMigrationTask(task.Task):
    """
    Task to migrate all keypairs from the source cloud to the target cloud.
    """

    def __init__(self, *args, **kwargs):
        super(KeypairMigrationTask, self).__init__(*args, **kwargs)
        # config must be ready at this point
        self.s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        self.t_cloud_name = cfg.CONF.TARGET.os_cloud_name
        self.s_host = cfg.CONF.SOURCE. \
            os_auth_url.split("http://")[1].split(":")[0]
        self.t_host = cfg.CONF.TARGET. \
            os_auth_url.split("http://")[1].split(":")[0]

    def migrate_one_keypair(self, keypair_fingerprint):
        values = [keypair_fingerprint, self.s_cloud_name, self.t_cloud_name]
        keypair_data = db_handler.get_keypairs(values)

        # check for resource duplication;
        # ignore the key pair if the same resource (with same fingerprint)
        # has already existed on the target cloud
        duplicated = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='nova',
                                       table_name='key_pairs',
                                       columns=['name'],
                                       filters={"deleted": '0',
                                                "fingerprint":
                                                keypair_fingerprint})

        if len(duplicated) > 0:
            LOG.info("Key pair {0} has been existed in cloud {1}, stop " \
                  "migrating this key pair.".format(keypair_data["name"],
                                             keypair_data["dst_cloud"]))
            # delete the corresponding assertion in the flyway database
            db_handler.delete_keypairs(values)
            return

        # check whether the owner (an user) of the key pair has existed on
        # the target cloud; stop migrating this key pair if the user is not
        # on the target cloud
        user_id_on_target = db_handler.\
            get_info_from_openstack_db(host=self.t_host,
                                       db_name='keystone',
                                       table_name='user',
                                       columns=['id'],
                                       filters={"name":
                                                keypair_data['user_name']})

        if len(user_id_on_target) < 1:
            LOG.info("The owner {0} has not been migrated to "
                     "the target, stop migrating key pair {1}".
                     format(keypair_data['user_name'], keypair_data['name']))
            # delete the corresponding assertion in the flyway database
            db_handler.delete_keypairs(values)
            return

        # check whether the owner of the key pair has the key pair with
        # the same name; ignore the key pair if its name is duplicated
        user_ids = db_handler.\
                   get_info_from_openstack_db(table_name="key_pairs",
                                              db_name='nova',
                                              host=self.t_host,
                                              columns=['user_id'],
                                              filters={"deleted": '0',
                                                       "name":
                                                       keypair_data["name"]})
        if len(user_ids) > 0:
            for one_id in user_ids:
                user_name = db_handler.\
                    get_info_from_openstack_db(table_name="user",
                                               db_name='keystone',
                                               host=self.t_host,
                                               columns=['name'],
                                               filters={"id": one_id[0]})
                if keypair_data["user_name"] == user_name[0][0]:
                    LOG.info("The user {0} has already own the key pair {1}, "
                             "stop migrating this key pair.".
                             format(user_name[0][0], keypair_data["name"]))
                    # delete the corresponding assertion in the flyway database
                    db_handler.delete_keypairs(values)
                    return

        # create a key pair by inserting the key pair data into the target cloud
        # 'key_pairs' table
        try:
            LOG.info("Creating key pair {0} on cloud {1}.".
                     format(keypair_data["name"], self.t_cloud_name))
            insert_values = {'created_at': strftime('%Y-%m-%d %H-%M-%S', localtime(time())),
                             'name': keypair_data['name'],
                             'user_id': user_id_on_target[0][0],
                             'fingerprint': keypair_data['fingerprint'],
                             'public_key': keypair_data['public_key'],
                             'deleted': '0'}

            db_handler.insert_info_to_openstack_db(host=self.t_host,
                                                   db_name='nova',
                                                   table_name='key_pairs',
                                                   values=[insert_values])

            keypair_data.update({'state': 'completed'})
            keypair_data.update({'user_id_updated': 1})

            LOG.info("Key pair {0} has been migrated to cloud {1} successfully.".
                     format(keypair_data["name"], self.t_cloud_name))

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

        db_handler.update_keypairs(**keypair_data)

    def execute(self, keypairs_to_move):
        # no resources need to be migrated
        if type(keypairs_to_move) is list and len(keypairs_to_move) == 0:
            return

        # in case only one string gets passed in
        if type(keypairs_to_move) is str:
            keypairs_to_move = [keypairs_to_move]

        # create new table if not exists
        db_handler.initialise_keypairs_mapping()

        if not keypairs_to_move:
            LOG.info("Start to migrate all key pairs ...")
            keypairs_to_move = []

            # get all keypairs from the table 'key_pairs' in 'nova'
            fingerprints = db_handler.\
                get_info_from_openstack_db(table_name="key_pairs",
                                           db_name='nova',
                                           host=self.s_host,
                                           columns=['fingerprint'],
                                           filters={"deleted": '0'})
            for one_fingerprint in fingerprints:
                keypairs_to_move.append(one_fingerprint[0])

        else:
            LOG.info("Start to migrate given key pairs of size {} ...\n"
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
                                               host=self.s_host,
                                               columns=['*'],
                                               filters={"fingerprint":
                                                        keypair_fingerprint})

                # get the corresponding user_name (in source)
                # of the keypair using user_id
                user_name = db_handler.\
                    get_info_from_openstack_db(table_name="user",
                                               db_name='keystone',
                                               host=self.s_host,
                                               columns=['name'],
                                               filters={"id": result[0][5]})

                keypair_data = {'name': result[0][4],
                                'public_key': result[0][7],
                                'fingerprint': result[0][6],
                                'user_name': user_name[0][0],
                                'src_cloud': self.s_cloud_name,
                                'dst_cloud': self.t_cloud_name,
                                'state': "unknown",
                                'user_id_updated': "0",
                                'new_name': None}
                db_handler.record_keypairs([keypair_data])

                LOG.info("Trying to migrate key pair '{}'\n".
                         format(result[0][4]))
                self.migrate_one_keypair(keypair_fingerprint)

            else:
                if m_keypair['state'] == "completed":
                    LOG.info("Key pair {0} in cloud {1} has already been "
                             "migrated".
                             format(m_keypair['name'], self.s_cloud_name))

                else:
                    LOG.info("Migrating key pair '{}'\n".
                             format(m_keypair['name']))
                    self.migrate_one_keypair(keypair_fingerprint)