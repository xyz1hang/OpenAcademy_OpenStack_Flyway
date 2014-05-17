
from taskflow import engines
from taskflow import task
from taskflow.patterns import linear_flow as lf
from taskflow.patterns import unordered_flow as uf

from flavortask import FlavorMigrationTask
from usertask import UserMigrationTask
from tenanttask import TenantMigrationTask
from roletask import RoleMigrationTask
from imagetask import ImageMigrationTask
from instancetask import InstanceMigrationTask
from keypairtask import KeypairMigrationTask
from update_projects_quotas_task import UpdateProjectsQuotasTask
from update_project_user_role_task import ProjectUserRoleBindingTask


class InputGatheringTask(task.Task):
    def __init__(self, inputs, **kwargs):
        super(InputGatheringTask, self).__init__(**kwargs)
        self.input_data = inputs if inputs else None

    def execute(self):
        if not self.input_data:
            self.input_data = {'users_to_move': None,
                               'tenants_to_move': None,
                               'flavors_to_migrate': None,
                               'images_to_migrate': None,
                               'tenant_to_process': None,
                               'keypairs_to_move': None,
                               'roles_to_migrate': None,
                               'tenant_vm_dicts': None}
        return self.input_data


def get_flow(input_data=None):
    input_task = InputGatheringTask(inputs=input_data)
    user_task = UserMigrationTask('user_migration_task')
    tenant_task = TenantMigrationTask('tenant_migration_task')
    flavor_task = FlavorMigrationTask('flavor_migration_task')
    role_task = RoleMigrationTask('role_migration_task')
    image_task = ImageMigrationTask('image_migration_task')
    instance_task = InstanceMigrationTask('instances_migration_task')
    keypair_task = KeypairMigrationTask('Keypairs_migration_task')

    proj_quota_task = UpdateProjectsQuotasTask('update_projects_quotas')
    pr_binding_task = ProjectUserRoleBindingTask('project_roles_bind_task')

    flow = lf.Flow('main_flow').add(
        task.FunctorTask(input_task.execute, provides={'users_to_move',
                                                       'tenants_to_move',
                                                       'flavors_to_migrate',
                                                       'images_to_migrate',
                                                       'tenant_to_process',
                                                       'keypairs_to_move',
                                                       'roles_to_migrate',
                                                       'tenant_vm_dicts'}),
        uf.Flow('user_tenant_migration_flow').add(
            # Note that creating users, tenants, flavor and role can happen in
            # parallel and hence it is part of unordered flow
            task.FunctorTask(user_task.execute, name='user_task',
                             rebind={'users_to_move': "users_to_move"}),
            task.FunctorTask(tenant_task.execute, name='tenant_task',
                             rebind={'tenants_to_move': "tenants_to_move"}),
            task.FunctorTask(flavor_task.execute, name='flavor_task',
                             rebind={
                                 'flavors_to_migrate': "flavors_to_migrate"}),
            task.FunctorTask(role_task.execute, name='role_task',
                             rebind={'roles_to_migrate': "roles_to_migrate"})
        ),
        # TODO: Add other tasks to the flow e.g migrate image, private key etc.
        task.FunctorTask(image_task.execute, name='image_task',
                         rebind={'images_to_migrate': "images_to_migrate",
                                 'tenant_to_process': 'tenant_to_process'}),
        task.FunctorTask(keypair_task.execute, name='keypair_task',
                         rebind={'keypairs_to_move': "keypairs_to_move"}),
        task.FunctorTask(instance_task.execute, name='instance_task',
                         rebind={'tenant_vm_dicts': "tenant_vm_dicts"}),

        # post migration task:
        task.FunctorTask(proj_quota_task.execute,
                         name='update_project_quota_task'),
        task.FunctorTask(pr_binding_task.execute,
                         name='project_role_binding_task')
    )

    return flow


def execute(input_data=None):
    print "input Data" + str(input_data) if input_data else "nothing"
    flow = get_flow(input_data)

    eng = engines.load(flow, engine_conf='parallel')
    result = eng.run()
    return result