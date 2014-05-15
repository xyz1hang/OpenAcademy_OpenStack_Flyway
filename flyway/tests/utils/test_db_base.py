from DBUtils.PooledDB import PooledDB, PooledDedicatedDBConnection
import MySQLdb
from tests.utils.test_base import TestBase
from utils.db_base import create_db_pool, create_database, connect, check_db_existed, delete_database
from common import config

__author__ = 'Sherlock'


class DBBaseTest(TestBase):
    def __init__(self, *args, **kwargs):
        super(DBBaseTest, self).__init__(*args, **kwargs)

    def test_create_db_pool(self):
        config.parse(['--config-file', '../../etc/flyway.conf'])
        db_name = 'flyway'
        create_database(db_name)
        create_db_pool(db_name)
        from utils.db_base import db_pool
        self.assertIsInstance(db_pool, PooledDB)

    def test_connect_without_db(self):
        config.parse(['--config-file', '../../etc/flyway.conf'])
        db_direct = connect(False)
        from MySQLdb.connections import Connection
        self.assertIsInstance(db_direct, Connection)

    def test_connect_with_db(self):
        config.parse(['--config-file', '../../etc/flyway.conf'])
        db_name = 'flyway'
        create_database(db_name)
        create_db_pool(db_name)
        db_from_pool = connect(True)
        self.assertIsInstance(db_from_pool, PooledDedicatedDBConnection)

    def test_check_db_exists(self):
        config.parse(['--config-file', '../../etc/flyway.conf'])
        existed_db_name = 'mysql'
        self.assertTrue(check_db_existed(existed_db_name))
        not_existed_db_name = 'db_name_that_should_not_exist'
        self.assertFalse(check_db_existed(not_existed_db_name))

    def test_delete_database(self):
        config.parse(['--config-file', '../../etc/flyway.conf'])
        db_name = 'db_name_that_should_not_exist'
        delete_database(db_name)
        self.assertFalse(check_db_existed(db_name))

    def test_create_database(self):
        config.parse(['--config-file', '../../etc/flyway.conf'])
        db_name = 'db_name_for_test'
        try:
            create_database(db_name)
            self.assertTrue(check_db_existed(db_name))
        except Exception, e:
            self.fail(e.message)
        finally:
            delete_database(db_name)
            self.assertFalse(check_db_existed(db_name))
