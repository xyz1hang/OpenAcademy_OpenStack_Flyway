from taskflow import task
from novaclient import exceptions as nova_exceptions

from utils import exceptions
from utils.helper import *
from utils.resourcetype import ResourceType
from utils.db_handlers import flavors


LOG = logging.getLogger(__name__)


class FlavorMigrationTask(task.Task):
    """
    Task to migrate all flavor settings from the source cloud to the
    target cloud.
    """

    def __init__(self, name, **kwargs):
        super(FlavorMigrationTask, self).__init__(name, **kwargs)
        # config must be ready at this point
        self.nv_source = get_nova_source()
        self.nv_target = get_nova_target()

        self.duplicates_handle = cfg.CONF.Duplicates_handle

        # create new table if not exists
        flavors.initialise_flavor_mapping()

    def migrate_one_flavor(self, flavor_name):
        try:
            s_flavor = self.nv_source.flavors.find(name=flavor_name)
        except nova_exceptions.NotFound:
            # encapsulate exceptions to make it more understandable
            # to user. Other exception handling mechanism can be added later
            LOG.error(exceptions.ResourceNotFoundException(
                ResourceType.flavor, flavor_name,
                cfg.CONF.SOURCE.os_cloud_name))
            return

        s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        # check whether the tenant has been migrated
        values = [flavor_name, s_flavor.id, s_cloud_name, t_cloud_name]
        m_flavor = flavors.get_migrated_flavor(values)
        new_flavor_name = flavor_name

        if m_flavor is not None and m_flavor['state'] == "completed":
            LOG.info("flavor {0} in cloud {1} has already been migrated"
                     .format(m_flavor["src_flavor_name"], s_cloud_name))
            return

        elif m_flavor is not None and m_flavor['state'] != "completed":
            LOG.info("Retrying migrating {0} from {1}"
                     .format(flavor_name, s_cloud_name))

        elif m_flavor is None:
            # check for tenant name duplication
            new_flavor_name = s_flavor.name
            try:
                if self.duplicates_handle == "SKIP":
                    found = self.nv_target.flavors.find(name=new_flavor_name)
                    if found:
                        LOG.info("Skipping flavor '{0}' duplicates"
                                 "found on cloud '{1}'"
                                 .format(found.name, t_cloud_name))
                        return

                elif self.duplicates_handle == "AUTO_RENAME":
                    found = True
                    while found:
                        found = self.nv_target.flavors.find(name=new_flavor_name)
                        if found:
                            new_flavor_name += "_migrated"

            except nova_exceptions.NotFound:
                # irrelevant exception swallow the exception
                pass

            # preparing record for inserting into database
            flavor_migration_data = {'src_flavor_name': s_flavor.name,
                                     'src_uuid': s_flavor.id,
                                     'src_cloud': s_cloud_name,
                                     'dst_flavor_name': new_flavor_name,
                                     'dst_uuid': "NULL",
                                     'dst_cloud': t_cloud_name,
                                     'state': "unknown"}
            
            flavors.record_flavor_migrated([flavor_migration_data])

            LOG.info("Start migrating flavour '{}'\n".format(s_flavor.name))

        new_flavor_details = {
            'name': new_flavor_name,
            'ram': s_flavor.ram,
            'vcpus': s_flavor.vcpus,
            'disk': s_flavor.disk,
            'ephemeral': s_flavor.ephemera if s_flavor.ephemeral else 0,
            'swap': s_flavor.swap if s_flavor.swap else 0,
            'rxtx_factor': s_flavor.rxtx_factor,
            'is_public': getattr(s_flavor,
                                 'os-flavor-access:is_public', False)}

        # create a new tenant
        flavour_data = flavors.get_migrated_flavor(values)
        try:
            migrated_flavor = self.nv_target.flavors.create(
                **new_flavor_details)

            flavour_data.update({'dst_uuid': migrated_flavor.id})

        except Exception as e:
            LOG.error("flavor '{}' migration failure\nDetails:"
                      .format(s_flavor.name, e.message))
            # update database record
            flavour_data.update({'state': "error"})
            flavors.update_migration_record(**flavour_data)
            return

        flavour_data.update({'state': "completed"})
        flavors.update_migration_record(**flavour_data)

    def execute(self, flavors_to_migrate):

        """execute the flavor migration task

        :param flavors_to_migrate: the names of flavors to migrate. If the not
        specified or length equals to 0 all flavor will be migrated,
        otherwise only specified flavor will be migrated
        """

        if flavors_to_migrate is None:
            LOG.info("Migrating all flavors ...")
            flavors_to_migrate = []
            for flavor in self.nv_source.flavors.list():
                flavors_to_migrate.append(flavor.name)
        # convert tenants_to_move to list in case only
        # one string gets passed in
        elif type(flavors_to_migrate) is str:
            flavors_to_migrate = [flavors_to_migrate]
        elif type(flavors_to_migrate) is list and len(flavors_to_migrate) > 0:
            LOG.info("Migrating given flavors of size {} ...\n"
                     .format(len(flavors_to_migrate)))
        elif type(flavors_to_migrate) is list and len(flavors_to_migrate) == 0:
            LOG.info("No flavour resources to be migrated.\n")
            return
        else:
            LOG.error("Incorrect parameter '{0}'.\n"
                      "Expects: a list of flavor names\n"
                      "Received: '{1}'".format("tenants_to_move",
                                               flavors_to_migrate))
            return

        for flavor in flavors_to_migrate:
            LOG.info("Migrating flavor '{}'\n".format(flavor))
            self.migrate_one_flavor(flavor)

    def revert(self, flavors_to_migrate):
        if flavors_to_migrate is None:
            LOG.info("Start reverting flavours.\n")
            flavors_to_migrate = []
            for flavor in self.nv_source.flavors.list():
                flavors_to_migrate.append(flavor.name)
        # convert tenants_to_move to list in case only
        # one string gets passed in
        elif type(flavors_to_migrate) is str:
            flavors_to_migrate = [flavors_to_migrate]
        elif type(flavors_to_migrate) is list \
                and len(flavors_to_migrate) == 0:
            LOG.info("No flavour resources to be reverted.\n")
            return
        elif type(flavors_to_migrate) is list \
                and len(flavors_to_migrate) > 0:
            LOG.info("Start reverting flavours.\n")
        else:
            LOG.error("Incorrect parameter '{0}'.\n"
                      "Expects: a list of flavor names\n"
                      "Received: '{1}'".format("tenants_to_move",
                                               flavors_to_migrate))
            return

        s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
        t_cloud_name = cfg.CONF.TARGET.os_cloud_name

        for flavor in flavors_to_migrate:
            try:
                s_flavor = self.nv_source.flavors.find(name=flavor)
            except nova_exceptions.NotFound:
                LOG.info("Do not need to revert flavour {0}, "
                         "since it does not exist in cloud {1} "
                         .format(flavor, s_cloud_name))
                return

            values = [flavor, s_flavor.id, s_cloud_name, t_cloud_name]
            flavor_data = flavors.get_migrated_flavor(values)

            if flavor_data is not None:
                if flavor_data["state"] == "completed":
                    try:
                        t_flavor = self.nv_target.flavors.\
                            find(name=flavor_data["dst_flavor_name"])
                        self.nv_target.flavors.delete(t_flavor)
                    except nova_exceptions.NotFound:
                        LOG.info("Do not need to revert flavour {0}, "
                                 "since it has not been migrated successfully"
                                 " to cloud {1}"
                                 .format(flavor_data["dst_flavor_name"],
                                         t_cloud_name))

                # delete record from flyway database
                flavors.delete_migration_record(values)
