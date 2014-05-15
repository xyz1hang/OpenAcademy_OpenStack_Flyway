import logging
import logging.config
import logging.handlers

from oslo.config import cfg


LOG = logging.getLogger(__name__)

opts = [
    cfg.StrOpt('os_auth_url', default=None),
    cfg.StrOpt('os_tenant_name', default='admin'),
    cfg.StrOpt('os_username', default='admin'),
    cfg.StrOpt('os_password'),
    cfg.StrOpt('os_cloud_name'),
    cfg.StrOpt('os_host_username'),
    cfg.StrOpt('os_host_password')
]

log_opts = [
    cfg.StrOpt('log_level', default='INFO'),
    cfg.StrOpt('log_file', default='./flyway.log'),
    cfg.StrOpt('log_format', default=None)
]

general_opts = {
    cfg.StrOpt('Duplicates_handle', default='SKIP')
}

db_opts = [
    cfg.StrOpt('host', default='localhost'),
    cfg.StrOpt('user', default='root'),
    cfg.StrOpt('mysql_password', default=None),
    cfg.StrOpt('db_name', default='flyway')
]

email_opts = [
    cfg.StrOpt('smtpserver', default='smtp.gmail.com:587'),
    cfg.StrOpt('login'),
    cfg.StrOpt('password')
]

scheduler_opts = [
    cfg.StrOpt('image_scheduler', default='DefaultImageScheduler'),
    cfg.StrOpt('vm_scheduler', default='DefaultVMScheduler')
]

CONF = cfg.CONF

source_group = cfg.OptGroup(name='SOURCE', title='Source OpenStack Options')
CONF.register_group(source_group)
CONF.register_opts(opts, source_group)

target_group = cfg.OptGroup(name='TARGET', title='Target OpenStack Options')
CONF.register_group(target_group)
CONF.register_opts(opts, target_group)

CONF.register_opts(general_opts)
CONF.register_opts(log_opts)

db_group = cfg.OptGroup(name='DATABASE', title='Database Credentials')
CONF.register_group(db_group)
CONF.register_opts(db_opts, db_group)

email_group = cfg.OptGroup(name='EMAIL', title='Email Credentials')
CONF.register_group(email_group)
CONF.register_opts(email_opts, email_group)

scheduler_group = cfg.OptGroup(name='SCHEDULER', title='Scheduler')
CONF.register_group(scheduler_group)
CONF.register_opts(scheduler_opts, scheduler_group)


def parse(args):
    cfg.CONF(args=args, project='flyway', version='0.1')
    

def setup_logging():
    logging.basicConfig(level=CONF.log_level)
    handler = logging.handlers.WatchedFileHandler(CONF.log_file, mode='a')
    formatter = logging.Formatter(CONF.log_format)
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    LOG.info("Logging enabled!")
