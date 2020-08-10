from main import create_roles, lend_book, return_book, register_user
from data import db_session, role, user, edition, library, book
import unittest
import os


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(AppTests, cls).setUpClass()
        db_session.global_init('db/tests.sqlite3')

    def test_create_roles(self):
        create_roles()
        session = db_session.create_session()
        roles = {x.name for x in session.query(role.Role).all()}
        self.assertEqual(roles, {'Student', 'Librarian'})
        session.commit()
        session.close()

    def test_register_user(self):
        create_roles()
        session = db_session.create_session()
        lib = library.Library(school_name='1')
        session.add(lib)
        session.commit()
        register_user('name', 'surname', 'login', 'password', 1, lib.id, 7)
        register_user('name', 'surname', 'login', 'password', 1, lib.id, 7)
        self.assertEqual(len(session.query(user.User).all()), 1)
        session.close()

    def tearDown(self) -> None:
        session = db_session.create_session()
        for i in (book.Book, edition.Edition, library.Library, role.Role, user.User):
            for j in session.query(i).all():
                session.delete(j)
        session.commit()
        session.close()

    @classmethod
    def tearDownClass(cls) -> None:
        super(AppTests, cls).tearDownClass()
        os.remove('db/tests.sqlite3')


if __name__ == '__main__':
    unittest.main()
