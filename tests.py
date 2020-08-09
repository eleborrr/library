from main import create_roles
from data import db_session, role
import unittest
import os


class AppTests(unittest.TestCase):
    def setUp(self):
        db_session.global_init('db/tests.sqlite3')

    def test_create_roles(self):
        create_roles()
        session = db_session.create_session()
        roles = {x.name for x in session.query(role.Role).all()}
        self.assertEqual(roles, {'Student', 'Librarian'})
        session.close()

    def tearDown(self):
        os.remove('db/tests.sqlite3')



if __name__ == '__main__':
    unittest.main()
