from DBUtils.PooledDB import PooledDB, PooledDedicatedDBConnection
from tests.utils.test_base import TestBase
from utils.db_base import create_db_pool, create_database, connect, check_db_exist, delete_database, check_table_exist, \
    create_table, delete_table, read_record, insert_record, delete_record, update_table, build_where_string, add_quotes, \
    check_record_exist, delete_all_data, release_db_pool

__author__ = 'Sherlock'


class DBBaseTest(TestBase):
    def __init__(self, *args, **kwargs):
        super(DBBaseTest, self).__init__(*args, **kwargs)

    def test_create_db_pool(self):

        db_name = 'flyway'
        create_database(db_name)
        create_db_pool(db_name)
        from utils.db_base import db_pool
        self.assertIsInstance(db_pool, PooledDB)

    def test_connect_without_db(self):
        db_direct = connect(False)
        from MySQLdb.connections import Connection
        self.assertIsInstance(db_direct, Connection)

    def test_connect_with_db(self):
        db_name = 'flyway'
        create_database(db_name)
        create_db_pool(db_name)
        db_from_pool = connect(True)
        self.assertIsInstance(db_from_pool, PooledDedicatedDBConnection)

    def test_check_db_exists(self):
        existed_db_name = 'mysql'
        self.assertTrue(check_db_exist(existed_db_name))
        not_existed_db_name = 'db_name_that_should_not_exist'
        self.assertFalse(check_db_exist(not_existed_db_name))

    def test_delete_database(self):
        db_name = 'db_name_that_should_not_exist'
        delete_database(db_name)
        self.assertFalse(check_db_exist(db_name))

    def test_create_database(self):
        db_name = 'db_name_for_test'
        try:
            create_database(db_name)
            self.assertTrue(check_db_exist(db_name))
        except Exception, e:
            self.fail(e.message)
        finally:
            delete_database(db_name)
            self.assertFalse(check_db_exist(db_name))

    def test_check_table_exist(self):
        db_name = 'mysql'
        release_db_pool()
        create_db_pool(db_name)
        not_existed_table_name = 'table_name_should_not_exist'
        self.assertFalse(check_table_exist(not_existed_table_name))
        exacted_table_name = 'user'
        self.assertTrue(check_table_exist(exacted_table_name))

    def test_delete_table(self):
        db_name = 'test'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'table_name_test'
        delete_table(table_name)
        self.assertFalse(check_table_exist(table_name))

    def test_create_table(self):
        db_name = 'test'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'test_table_name'
        try:
            create_table(table_name, 'id varchar(20)', True)
            self.assertTrue(check_table_exist(table_name))
        except Exception, e:
            self.fail(e.message)
        finally:
            delete_table(table_name)
            self.assertFalse(check_table_exist(table_name))

    def test_read_record(self):
        db_name = 'mysql'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'user'
        data = read_record(table_name,
                           ['*'],
                           {'Host': 'localhost', 'User': 'root'},
                           True)
        self.assertEqual('localhost', data[0][0])
        self.assertEqual('root', data[0][1])

    def test_check_record_exist(self):
        db_name = 'mysql'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'user'
        result = check_record_exist(table_name,
                                    {'Host': 'localhost', 'User': 'root'})
        self.assertTrue(result)

        result = check_record_exist(table_name,
                                    {'Host': 'localhost', 'User': 'not_exist_user'})
        self.assertFalse(result)

    def test_insert_record(self):
        db_name = 'test'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'test_table_name'
        create_table(table_name, 'id varchar(20)', True)
        test_id = 1
        try:
            insert_record(table_name, [{'id': test_id}], True)
            data = read_record(table_name, ['id'], {'1': 1}, True)
            self.assertIn((str(test_id),), data)
        except Exception, e:
            self.fail(e.message)
        finally:
            delete_table(table_name)

    def test_delete_some_record(self):
        db_name = 'test'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'test_table_name'
        create_table(table_name, 'id varchar(20)', True)
        test_id, test_id2 = 1, 2
        insert_record(table_name, [{'id': test_id}, {'id': test_id2}], True)
        data = read_record(table_name, ['id'], {'1': 1}, True)
        self.assertIn((str(test_id),), data)
        self.assertIn((str(test_id2),), data)
        try:
            delete_record(table_name, {'id': test_id})
            data = read_record(table_name, ['id'], {'1': 1}, True)
            self.assertNotIn((str(test_id)), data)
            self.assertIn((str(test_id2),), data)
        except Exception, e:
            self.fail(e)
        finally:
            delete_table(table_name)

    def test_delete_all_record(self):
        db_name = 'test'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'test_table_name'
        create_table(table_name, 'id varchar(20)', True)
        test_id, test_id2 = 1, 2
        insert_record(table_name, [{'id': test_id}, {'id': test_id2}], True)
        data = read_record(table_name, ['id'], {'1': 1}, True)
        self.assertIn((str(test_id),), data)
        self.assertIn((str(test_id2),), data)
        try:
            delete_record(table_name, None)
            data = read_record(table_name, ['id'], {'1': 1}, True)
            self.assertNotIn((str(test_id)), data)
            self.assertNotIn((str(test_id2),), data)
        except Exception, e:
            self.fail(e)
        finally:
            delete_table(table_name)

    def test_update_table(self):
        db_name = 'test'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'test_table_name'
        create_table(table_name, 'id varchar(20)', True)
        test_id, test_id2 = 1, 2
        insert_record(table_name, [{'id': test_id}], True)
        data = read_record(table_name, ['id'], {'1': 1}, True)
        self.assertIn((str(test_id),), data)
        self.assertNotIn((str(test_id2),), data)
        try:
            update_table(table_name, {'id': test_id2}, {'id': test_id}, True)
            data = read_record(table_name, ['id'], {'1': 1}, True)
            self.assertIn((str(test_id2),), data)
            self.assertNotIn((str(test_id),), data)
        except Exception, e:
            self.fail(e)
        finally:
            delete_table(table_name)

    def test_build_where_string(self):
        where_dict = {'id': 3}
        self.assertEqual('id = \'3\'',
                         build_where_string(where_dict))

        where_dict = {'id': 3, 'name': 'John'}
        self.assertEqual('id = \'3\' AND name = \'John\'',
                         build_where_string(where_dict))

    def test_add_quotes(self):
        string = '234'
        self.assertEqual('\'234\'', add_quotes(string))

    def test_delete_all_data(self):
        db_name = 'test'
        release_db_pool()
        create_db_pool(db_name)
        table_name = 'test_table_name'
        create_table(table_name, 'id varchar(20)', True)
        test_id, test_id2 = 1, 2
        insert_record(table_name, [{'id': test_id}, {'id': test_id2}], True)
        data = read_record(table_name, ['id'], {'1': 1}, True)
        self.assertIn((str(test_id),), data)
        self.assertIn((str(test_id2),), data)
        try:
            delete_all_data(table_name)
            data = read_record(table_name, ['id'], {'1': 1}, True)
            self.assertNotIn((str(test_id)), data)
            self.assertNotIn((str(test_id2),), data)
        except Exception, e:
            self.fail(e)
        finally:
            delete_table(table_name)
