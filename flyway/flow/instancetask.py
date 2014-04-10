from taskflow import task

from utils.helper import *


LOG = logging.getLogger(__name__)


class InstanceMigrationTask(task.Task):
    """
    Task to migrate all instances from the source cloud to the target cloud.
    """

    def execute(self):
        LOG.info('Migrating all instances ...')

        ks_source_credentials = get_source_credentials()
        ks_target_credentials = get_target_credentials()

        ks_source = get_keystone_client(**ks_source_credentials)
        ks_target = get_keystone_client(**ks_target_credentials)

        #Connect to source cloud nova
        invisible_tenant_names = ['invisible_to_admin',
                                  'alt_demo',
                                  'service']

        for tenant in ks_source.tenants.list():
            if tenant.name not in invisible_tenant_names:
                nv_source_credentials = get_source_credentials()
                nv_target_credentials = get_target_credentials()

                nv_source = get_nova_client(**nv_source_credentials)
                nv_target = get_nova_client(**nv_target_credentials)

                #Obtain all instances names per tenant in target cloud
                target_instanceNames = []
                for instance in nv_target.servers.list():
                    target_instanceNames.append(instance.name)

            # FIXME: Python does not have such block comments. Prepend a # to
            # FIXME: each line to block comment
            """
			Check whether the instance from source cloud has existed in the target cloud
			If not, migrate instances into corresponding tenant
			"""
            for instance in nv_source.servers.list():
                if instance.name not in target_instanceNames:
                    image = nv_target.images.find(name=nv_source.images.get(
                        instance.image['id']).name)
                    image_id = str(image.id)
                    flavor = nv_target.flavors.find(
                        name=nv_source.flavors.get(
                            instance.flavor['id']).name)
                    nv_target.servers.create(name=instance.name,
                                             image=image_id,
                                             flavor=flavor,
                                             key_name=instance.key_name,
                                             security_groups=['default'])
                                        #use the security_groups 'default'

            for instance in nv_target.servers.list():
                LOG.debug(instance)
