from testtools import TestCase
from task_scheduler.scheduler import setup_scheduler
from utils.db_base import create_database, create_db_pool, release_db_pool
from utils.db_handlers import environment_config
from common import config


__author__ = 'hydezhang'


class TestBase(TestCase):
    """base class of tests. Please put all common logic here (setup etc.)

    """

    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        config.parse(['--config-file', './etc/flyway.conf'])
        setup_scheduler()

        db_name = 'flyway'
        create_database(db_name)
        release_db_pool()
        create_db_pool(db_name)