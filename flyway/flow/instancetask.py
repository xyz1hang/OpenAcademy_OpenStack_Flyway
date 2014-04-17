import logging
from taskflow import task
from utils import db_handler

from utils.helper import *


LOG = logging.getLogger(__name__)


class InstanceMigrationTask(task.Task):
    """
    Task to migrate all instances from the source cloud to the target cloud.
    """

    def __init__(self, **kwargs):
        super(InstanceMigrationTask, self).__init__(**kwargs)
        self.ks_source = get_keystone_source()
        self.ks_target = get_keystone_target()

    def create_vm(self, server, source_nova_client, target_nova_client,
                  source_cloud_name):

        # preparing flavor
        original_flavor_id = "'"+server.flavor['id']+"'"
        original_flavor = source_nova_client.flavors.find(id=original_flavor_id)
        filter_values = [original_flavor.name, original_flavor.id,
                         source_cloud_name]
        migrated_flavor = db_handler.get_migrated_flavor(filter_values)

        if not migrated_flavor:
            print("The required flavor hasn't been migrated yet.")
            return None

        dst_flavor_id = "'" + migrated_flavor.dst_uuid + "'"
        flavor_to_use = target_nova_client.flavors.find(id=dst_flavor_id)

        # preparing image
        original_image_id = "'"+server.image['id']+"'"
        original_image = source_nova_client.images.find(id=original_image_id)
        filter_values = [original_image.name, original_image.id,
                         source_cloud_name]

        migrated_image = db_handler.get

    def create_proxy_vm(self, server, source_nova_client, target_nova_client):

        valid_states = ['ACTIVE', 'PAUSED', 'SUSPENDED', 'SHUTOFF']

        instance_state = getattr(server, 'status')
        if instance_state in valid_states:
            s_cloud_name = cfg.CONF.SOURCE.os_cloud_name
            t_cloud_name = cfg.CONF.TARGET.os_cloud_name

            src_tenant = source_nova_client.projectid
            dst_tenant = target_nova_client.projectid

            # check whether the vm has been migrated
            values = [server.name, src_tenant, s_cloud_name]
            instances = db_handler.get_migrated_vm(values)

            instance = instances[0] if instances else None
            if instance:
                if instance.dst_uuid and \
                   instance.migration_state is "completed":
                    print "VM[%s,%s] has been migrated" % \
                          (instance.src_uuid, instance.src_server_name)
                    return
                if instance.dst_uuid and \
                   instance.migration_state is not "launched_proxy":
                    return

            print "creating proxy instance in destination cloud for " \
                  "instance '%s' with source id '%s'"\
                  % (server.name, server.id)

            try:
                instance_migration_data = {
                    'src_server_name': server.name,
                    'src_uuid': server.id,
                    'src_cloud': s_cloud_name,
                    'src_tenant': src_tenant,
                    'dst_cloud': t_cloud_name,
                    'dst_tenant' : dst_tenant,
                    'state': instance_state,
                    'status': 'launching_proxy'}

                db_handler.record_vm_migrated(**instance_migration_data)

                time.sleep(5)
                d_server = create_vm(src_cloud, dst_cloud,
                                     s_tenant, d_tenant,
                                     server.id, **kwargs)

                dbapi.update_vm_mapping(instance, {
                    'dst_server_name': d_server.name,
                    'dst_uuid': d_server.id,
                    'status': 'launched_proxy'
                })

                # migrate key data for this instance
                dbapi.set_instance_key_data(d_server.id)
                dbapi.migrate_instance_metadata(src_cloud, dst_cloud,
                                                d_server.id)

                d_servers.append(d_server)
                id_to_server_map[server.id] = server
                id_to_server_map[d_server.id] = d_server

            except Exception as e:
                print "VM[%s] creation ended up in exception %s" % \
                      (server.name, str(e))
                dbapi.update_vm_mapping(instance,
                                        {'state': 'error',
                                         'data': traceback.format_exc(e)})
                traceback.print_exc()
        else:
            message = 'ignoring vm %s due to state %s' % \
                      (server.name, getattr(server, 'status'))
            print message
            skip_server(src_cloud, tenant_name, server, message)

    def execute(self, tenant_vm_dicts=None):

        """execute instance migration task

        :param tenant_vm_dict: a dictionary which provides the tenant and
        particular instances of the tenant desired to migrate

        structure:
        ---- tenant_name: vm_lists
        ---- tenant_name: vm_lists
        ---- ...
        """
        vm_to_migrate = []
        if not tenant_vm_dicts:
            LOG.info('Migrating instances for all tenants...')
            for tenant in self.ks_source.tenants.list():
                source_nova = get_nova_source(tenant)

                target_tenant = db_handler.get_migrated_vm(tenant)
                if not target_tenant[0]:
                    print ("The tanent of this instance hasn't been ")

                for server in source_nova.servers.list():
                    self.create_proxy_vm(server, source_nova)

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
